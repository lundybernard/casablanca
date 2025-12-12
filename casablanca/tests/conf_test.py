from unittest import TestCase
from unittest.mock import patch

from dataclasses import dataclass
from configparser import ConfigParser

from ..conf import (
    get_config,
    Namespace,
)


SRC = 'casablanca.conf'

EXAMPLE_CONFIG_INI = '''
[batconf]
default_env = example

[example]
[example.casablanca]
key = value
[example.casablanca.remote_host]
api_key = example_api_key
url = https://api-example.host.io/

[alt]
[alt.casablanca]
[alt.casablanca.module]
key = alt_value
'''

CONFIG_PARSER_ENVS = ConfigParser()
CONFIG_PARSER_ENVS.read_string(EXAMPLE_CONFIG_INI)

class Test_get_config(TestCase):

    def setUp(t):
        patches = ['IniConfig', ]
        for target in patches:
            patcher = patch(f'{SRC}.{target}', autospec=True)
            setattr(t, target, patcher.start())
            t.addCleanup(patcher.stop)

        t.config_file_data = {
            'default': 'test_config',
            'test_config': {
                'casablanca': {
                    'AModule': {
                        'arg_1': 'conf_file_arg_1',
                        'arg_2': 'conf_file_arg_2',
                    },
                    'BModule': {'arg_1': '2020-20-21', },
                }
            }
        }

        @dataclass
        class ConfA:
            arg_1: str = 'dataclass_default_arg_1'
            arg_2: str = 'dataclass_default_arg_2'
            arg_3: str = 'dataclass_default_arg_3'

        @dataclass
        class ConfB:
            arg_1: str = 'dataclass_default_isodate'

        @dataclass
        class ConfigSchema:
            AModule: ConfA
            BModule: ConfB
            config_file: str = './config.ini'

        t.ConfigSchema = ConfigSchema

    def test_without_parameters(t):
        _ = get_config()

    @patch(f'{SRC}.EnvConfig', autospec=True)
    def test_default_values(t, EnvConfig):
        t.IniConfig.return_value = None
        EnvConfig.return_value = None

        CONF = get_config(t.ConfigSchema)

        t.assertEqual(CONF.AModule.arg_3, 'dataclass_default_arg_3')
        t.assertEqual(CONF.BModule.arg_1, 'dataclass_default_isodate')

    def test_arg_cli_args(t):
        cli_args = Namespace()
        setattr(cli_args, 'casablanca.AModule.arg_1', 'cli_arg_1')

        conf = get_config(t.ConfigSchema, cli_args=cli_args)
        print(conf)
        t.assertEqual(conf.AModule.arg_1, 'cli_arg_1')

    def test_arg_config_file(t):
        '''The given config_file parameter is used for attribute lookups
        '''
        config_file = t.IniConfig.return_value
        conf = get_config(t.ConfigSchema, config_file=config_file)

        t.assertEqual(conf.AModule.arg_1, config_file.get.return_value)
        config_file.get.assert_called_with(
            'arg_1',
            'casablanca.AModule',
        )

    def test_arg_config_file_name(t):
        '''The given config_file_name is passed to the IniConfig constructor
        '''
        config_file_name = './test.config.yaml'
        get_config(
            t.ConfigSchema, config_file_name=config_file_name
        )
        t.IniConfig.assert_called_with(config_file_name, config_env=None)

    def test_arg_config_env(t):
        '''The given config_env name is passed to the IniConfig constructor
        '''
        config_env = 'configuration file environment'
        get_config(t.ConfigSchema, config_env=config_env)
        t.IniConfig.assert_called_with('.config.ini', config_env=config_env)

    @patch(f'{SRC}.EnvConfig', autospec=True)
    def test__getattr__missing_attribute(t, EnvConfig):
        t.IniConfig.return_value = None
        EnvConfig.return_value = None

        conf = get_config(t.ConfigSchema)
        with t.assertRaises(AttributeError):
            conf._sir_not_appearing_in_this_film
