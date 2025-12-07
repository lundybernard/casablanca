from unittest import TestCase
from unittest.mock import patch, Mock

from ..cli import (
    argparser,
    BATCLI,
    NestedNameSpace,
    Commands,
    logging,
    argparse,
)


SRC = 'casablanca.cli'


class TestArgparser(TestCase):

    def test_argparser(t):
        argparser()


class TestBATCLI(TestCase):

    def setUp(t):
        patches = ['exit', 'get_config', ]
        for target in patches:
            patcher = patch(f'{SRC}.{target}', autospec=True)
            setattr(t, target, patcher.start())
            t.addCleanup(patcher.stop)

    def validate_commands(t, commands):
        for cmd in commands:
            with t.subTest(cmd):
                func = '_'.join(cmd.split())
                with patch(f'{SRC}.Commands.{func}', autospec=True) as m_cmd:
                    m_cmd.__name__ = func
                    ARGS = cmd.split()
                    BATCLI(ARGS)
                    args = argparser().parse_args(ARGS)
                    t.get_config.assert_called_with(
                        cli_args=args,
                        config_file=args.config_file,
                        config_env=args.config_env,
                    )
                    m_cmd.assert_called_with(
                        t.get_config.return_value
                    )
                    t.exit.assert_called_with(0)

    @patch(f'{SRC}.Commands.set_log_level', autospec=True)
    def test_set_log_level(t, set_log_level):
        args = ['--debug', 'hello', ]
        BATCLI(args)
        set_log_level.assert_called_with(argparser().parse_args(args))
        t.exit.assert_called_with(0)


    @patch('builtins.print')
    @patch(f'{SRC}.argparser', autospec=True)
    def test_command_error(t, argparser, print):
        '''prints the error message, and help if a command throws an error
        '''
        ARGS = []
        exc = RuntimeError()

        def fail(_):
            raise exc

        args = Mock(['func', 'loglevel'])
        args.loglevel = 0
        args.func = fail
        parser = Mock()
        parser.parse_args.return_value = args
        argparser.return_value = parser

        with t.assertRaises(RuntimeError):
            BATCLI(ARGS)

    def test_commands(t):
        commands = [
            'hello',
            'run_functional_tests',
            'run_container_tests',
        ]

        t.validate_commands(commands)

    # TODO: full coverage of CLI arguments that trigger commands


class TestNestedNameSpace(TestCase):

    def test_nesting(t):
        nns = NestedNameSpace()
        setattr(nns, 'top', 'level')
        setattr(nns, 'bat.baz', 'baz')
        setattr(nns, 'bat.sub.var', 'sub_var')

        t.assertEqual(nns.top, 'level')
        t.assertEqual(nns.bat.baz, 'baz')
        t.assertEqual(nns.bat.sub.var, 'sub_var')


class TestCommands(TestCase):

    @patch(f'{SRC}.log', autospec=True)
    def test_set_log_level(t, log):
        with t.subTest('default to ERROR'):
            args = argparse.Namespace(loglevel=logging.INFO)
            Commands.set_log_level(args)
            log.setLevel.assert_called_with(logging.INFO)

        with t.subTest('set given value'):
            args = argparse.Namespace(loglevel=logging.INFO)
            Commands.set_log_level(args)
            log.setLevel.assert_called_with(logging.INFO)
