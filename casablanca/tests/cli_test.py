from unittest import TestCase
from unittest.mock import patch, Mock

from ..cli import (
    argparser,
    BATCLI,
    NestedNameSpace,
    Commands,
    logging,
    argparse,
    get_help,
)


SRC = 'casablanca.cli'


class CliTests(TestCase):
    def test_argparser(t):
        argparser()

    def test_get_help(t):
        parser = Mock()

        help_func = get_help(parser)
        help_func('args placeholder')
        parser.print_help.assert_called_once()


class TestBATCLI(TestCase):
    def setUp(t):
        patches = [
            'exit',
            'get_config',
        ]
        for target in patches:
            patcher = patch(f'{SRC}.{target}', autospec=True)
            setattr(t, target, patcher.start())
            t.addCleanup(patcher.stop)

        t.cfg = t.get_config.return_value
        t.cfg.loglevel = 0

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
                        config_file_name=args.config_file,
                        config_env=args.config_env,
                    )
                    m_cmd.assert_called_with(t.get_config.return_value)
                    t.exit.assert_called_with(0)

    @patch(f'{SRC}.argparser', autospec=True)
    @patch(f'{SRC}.Commands.set_log_level', autospec=True)
    def test_set_log_level(
        t,
        set_log_level: Mock,
        argparser: Mock,
    ):
        ARGS = [
            '--debug',
            'hello',
        ]
        parser = argparser.return_value
        args = parser.parse_args.return_value
        args.func = Commands.hello

        BATCLI(ARGS)

        parser.parse_args.assert_called_with(args=ARGS)
        t.get_config.assert_called_with(
            cli_args=args,
            config_file_name=args.config_file,
            config_env=args.config_env,
        )
        set_log_level.assert_called_with(t.cfg)
        t.exit.assert_called_with(0)

    def test_commands(t):
        commands = [
            'hello',
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
