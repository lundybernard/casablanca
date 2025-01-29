from unittest import TestCase
from unittest.mock import patch

from dataclasses import dataclass

import yaml

from ..conf import (
    get_config,
    Namespace,
)


SRC = 'bat.conf'

EXAMPLE_CONFIG_YAML = '''
default: example

example:
    bat:
        key: value
        remote_host:
            api_key: example_api_key
            url: https://api-example.host.io/

alt:
    bat:
        module:
            key: alt_value
'''

EXAMPLE_CONFIG_DICT = yaml.load(EXAMPLE_CONFIG_YAML, Loader=yaml.BaseLoader)


class Test_get_config(TestCase):

    def setUp(t):
        patches = ['FileConfig', ]
        for target in patches:
            patcher = patch(f'{SRC}.{target}', autospec=True)
            setattr(t, target, patcher.start())
            t.addCleanup(patcher.stop)

        t.config_file_data = {
            'default': 'test_config',
            'test_config': {
                'bat': {
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

        #  As if imported from a module
        ConfA.__module__ = 'bat.AModule'
        ConfB.__module__ = 'bat.BModule'

        @dataclass
        class GlobalConfig:
            AModule: ConfA
            BModule: ConfB
            config_file: str = './GlobalConfig.yaml'

        GlobalConfig.__module__ = 'bat'
        t.GlobalConfig = GlobalConfig

    @patch(f'{SRC}.EnvConfig', autospec=True)
    def test_default_values(t, EnvConfig):
        t.FileConfig.return_value = None
        EnvConfig.return_value = None

        CONF = get_config(t.GlobalConfig)

        t.assertEqual(CONF.AModule.arg_3, 'dataclass_default_arg_3')
        t.assertEqual(CONF.BModule.arg_1, 'dataclass_default_isodate')

    def test_arg_cli_args(t):
        cli_args = Namespace(arg_1='cli_arg_1')

        conf = get_config(t.GlobalConfig, cli_args=cli_args)

        t.assertEqual(conf.AModule.arg_1, 'cli_arg_1')

    def test_arg_config_file(t):
        '''The given config_file parameter is used for attribute lookups
        '''
        config_file = t.FileConfig.return_value
        conf = get_config(t.GlobalConfig, config_file=config_file)

        t.assertEqual(conf.AModule.arg_1, config_file.get.return_value)
        config_file.get.assert_called_with('arg_1', module='bat.AModule')

    def test_arg_config_file_name(t):
        '''The given config_file_name is passed to the FileConfig constructor
        '''
        config_file_name = './test.config.yaml'
        get_config(
            t.GlobalConfig, config_file_name=config_file_name
        )
        t.FileConfig.assert_called_with(config_file_name, config_env=None)

    def test_arg_config_env(t):
        '''The given config_env name is passed to the FileConfig constructor
        '''
        config_env = 'configuration file environment'
        get_config(t.GlobalConfig, config_env=config_env)
        t.FileConfig.assert_called_with(None, config_env=config_env)

    @patch(f'{SRC}.EnvConfig', autospec=True)
    def test__getattr__missing_attribute(t, EnvConfig):
        t.FileConfig.return_value = None
        EnvConfig.return_value = None

        conf = get_config(t.GlobalConfig)
        with t.assertRaises(AttributeError):
            conf._sir_not_appearing_in_this_film
