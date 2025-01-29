import argparse


# TODO: Convert this into a ArgumentParser object, and make them composable
def server_parser():
    parser = argparse.ArgumentParser(
        prog='server',
        description='http server related commands',
    )
    parser.set_defaults(func=get_help(parser))

    parser.add_argument(
        '-H', '--host', dest='server.host',
        default='0.0.0.0',
        help='host ip on which the service will be made available',
    )
    parser.add_argument(
        '-P', '--port', dest='server.port',
        default='5000',
        help='port on which the service will be made available'
    )
    parser.add_argument(
        '-d', '--debug', dest='server.debug',
        default=True,
        help='run web service with debug level output'
    )

    commands = parser.add_subparsers(
        dest='server.command',
        title='server commands',
        help='server control commands',
    )
    # start args
    start_cmd = commands.add_parser(
        'start',
        description='start the web server',
        help='for details use start --help',
    )
    start_cmd.set_defaults(func=start)

    test_cmd = commands.add_parser(
        'test',
        description='run functional tests',
        help='for details use test --help'
    )
    test_cmd.set_defaults(func=test)

    return parser


def get_help(parser):
    def help(conf):
        parser.print_help()
    return help


def start(conf):
    from .server import start_api_server
    start_api_server(
        host=conf.server.host,
        port=conf.server.port,
        debug=conf.server.debug,
    )


def test(args):
    print('++ run functional tests ++')
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover('functional_tests', pattern='*_test.py')
    runner = unittest.TextTestRunner()
    runner.run(suite)
