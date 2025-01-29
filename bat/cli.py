import argparse
import logging
from logging.config import dictConfig
from sys import exit

from bat.conf import get_config

from bat.server import server_parser
from bat.example.cli import example_cli
from bat.logconf import logging_config
from bat.lib import hello_world


dictConfig(logging_config)
log = logging.getLogger('root')


def BATCLI(ARGS=None):
    p = argparser()
    # Execute
    # get only the first command in args
    args = p.parse_args(ARGS, NestedNameSpace())
    conf = get_config(
        cli_args=args,
        config_file=args.config_file,
        config_env=args.config_env,
    )
    Commands.set_log_level(args)
    # execute function set for parsed command
#    if not hasattr(Commands, args.func.__name__):
    try:
        args.func(conf)
    except Exception as exp:
        print(exp)
        p.print_help()
        exit(1)
    exit(0)


class NestedNameSpace(argparse.Namespace):
    def __setattr__(self, name, value):
        if '.' in name:
            group, name = name.split('.', 1)
            ns = getattr(self, group, NestedNameSpace())
            setattr(ns, name, value)
            self.__dict__[group] = ns
        else:
            self.__dict__[name] = value


def argparser():
    p = argparse.ArgumentParser(
        description='Utility for executing various bat tasks',
        usage='bat [<args>] <command>',
    )
    p.set_defaults(func=get_help(p))

    p.add_argument(
        '-v', '--verbose',
        help='enable INFO output',
        action='store_const',
        dest='loglevel',
        const=logging.INFO
    )
    p.add_argument(
        '--debug',
        help='enable DEBUG output',
        action='store_const',
        dest='loglevel',
        const=logging.DEBUG,
    )
    p.add_argument(
        '-c', '--conf', '--config_file',
        dest='config_file',
        default=None,
        help='specify a config file to get environment details from.'
             ' default=./config.yaml',
    )
    p.add_argument(
        '-e', '--env', '--config_environment',
        dest='config_env',
        default=None,
        help='specify the remote environment to use from the config file',
    )

    # Add a subparser to handle sub-commands
    commands = p.add_subparsers(
        dest='command',
        title='commands',
        description='for additonal details on each command use: '
                    '"bat {command name} --help"',
    )
    # hello args
    hello = commands.add_parser(
        'hello',
        description='execute command hello',
        help='for details use hello --help',
    )
    hello.set_defaults(func=Commands.hello)

    commands.add_parser(
        'server',
        help='http server related commands',
        add_help=False,
        parents=[server_parser()],
    )
    # Add a subparser from a module
    commands.add_parser(
        'example',
        help='example module commands',
        add_help=False,
        parents=[example_cli()],
    )

    testing_cli(commands)

    return p


def get_help(parser):
    def help(args):
        parser.print_help()
    return help


def testing_cli(subparser):
    # run_functional_tests args
    run_functional_tests = subparser.add_parser(
        'run_functional_tests',
        description='start the server locally and run functional tests',
        help='for details use test --help'
    )
    run_functional_tests.set_defaults(func=Commands.run_functional_tests)
    run_functional_tests.add_argument(
        '-H', '--host', dest='host',
        default='0.0.0.0',
        help='host ip on which the service will be run',
    )
    run_functional_tests.add_argument(
        '-P', '--port', dest='port',
        default='5000',
        help='port on which the service service will be run'
    )

    # run_functional_tests args
    run_container_tests = subparser.add_parser(
        'run_container_tests',
        description='start docker-compose and run functional tests',
        help='for details use test --help'
    )
    run_container_tests.set_defaults(func=Commands.run_container_tests)
    run_container_tests.add_argument(
        '-H', '--host', dest='host',
        default='0.0.0.0',
        help='host ip on which the service will be run',
    )
    run_container_tests.add_argument(
        '-P', '--port', dest='port',
        default='5000',
        help='port on which the service service will be run'
    )


class Commands:

    @staticmethod
    def hello(conf):
        print(hello_world())

    @staticmethod
    def set_log_level(conf):
        if conf.loglevel:
            log.setLevel(conf.loglevel)
        else:
            log.setLevel(logging.ERROR)

    @staticmethod
    def run_functional_tests(conf):
        import subprocess
        import os
        import signal
        from time import sleep
        a = subprocess.Popen(['bat', 'start'])
        sleep(0.5)
        Commands.test(conf)

        os.kill(a.pid, signal.SIGTERM)

    @staticmethod
    def run_container_tests(conf):
        import subprocess
        import os
        import signal
        from time import sleep
        a = subprocess.Popen(['docker-compose', 'up'])
        sleep(0.5)
        Commands.test(conf)

        os.kill(a.pid, signal.SIGTERM)
        sleep(0.5)

    @staticmethod
    def test(conf):
        print('++ run functional tests ++')
        import unittest
        loader = unittest.TestLoader()
        suite = loader.discover('functional_tests', pattern='*_test.py')
        runner = unittest.TextTestRunner()
        runner.run(suite)
