from unittest import TestCase
from unittest.mock import patch, Mock

from ..cli import (
    server_parser,

)


SRC = 'bat.server.cli'


class Test_server_parser(TestCase):

    def test_server_parser(t):
        server_parser()

    def validate_commands(t, commands):
        for cmd in commands:
            with t.subTest(cmd):
                with patch(f'{SRC}.{cmd}', autospec=True) as m_cmd:
                    m_cmd.__name__ = cmd
                    ARGS = cmd.split()
                    args = server_parser().parse_args(ARGS)
                    print(args)
                    t.assertEqual(args.func, m_cmd)

    def test_missing_command(t):
        '''prints help if no arguments are given
        '''
        ARGS = []
        parser = server_parser()
        parser.print_help = Mock(wraps=parser.print_help)
        args = parser.parse_args(ARGS)

        args.func(args)
        parser.print_help.assert_called_with()

    def test_commands(t):
        commands = [
            'start',
            'test',
        ]

        t.validate_commands(commands)
