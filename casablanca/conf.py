from typing import Any
from dataclasses import dataclass

from .example import Config as ExampleConfig

from batconf.manager import Configuration, ConfigProtocol

from batconf.source import SourceList
from batconf.sources.args import CliArgsConfig, Namespace
from batconf.sources.env import EnvConfig
from batconf.sources.file import FileConfig
from batconf.sources.dataclass import DataclassConfig



@dataclass
class ConfigSchema:
    # example module with configuration dataclass
    example: ExampleConfig


def get_config(
    # Known issue: https://github.com/python/mypy/issues/4536
    config_class: ConfigProtocol | Any = ConfigSchema,
    cfg_path: str = 'casablanca',
    cli_args: Namespace | None = None,
    config_file: SourceInterface | None = None,
    config_file_name: str = None,
    config_env: str | None = None,
) -> Configuration:

    # Build a prioritized config source list
    config_sources = [
        NamespaceConfig(cli_args) if cli_args else None,
        EnvConfig(),
        (
            config_file if config_file
            else FileConfig(config_file_name, config_env=config_env)
        ),
    ]

    source_list = SourceList(config_sources)

    return Configuration(source_list, config_class, path=cfg_path)
