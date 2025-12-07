from unittest import TestCase
from unittest.mock import patch, Mock, call
from bat.example.cli import (
    hello_world,
    get_help,
    default,
    argparse,
    Configuration,
)


class ExampleTests(TestCase):

    @patch('builtins.print')
    def test_hello_world(t: TestCase, print: Mock):
        conf = Mock(Configuration)
        hello_world(conf)
        print.assert_called_with('Hello from the example module!')

    def test_get_help(t: TestCase):
        parser = Mock(argparse.ArgumentParser)
        conf = Mock(Configuration)

        helper = get_help(parser)
        helper(conf)

        parser.print_help.assert_called_with()

    @patch('builtins.print')
    def test_default(t: TestCase, print: Mock):
        conf = Mock(Configuration)
        default(conf)
        print.assert_has_calls([
            call('default response from example module CLI'),
            call(f'{conf=}'),
        ])
