from bat import GlobalConfig

from batconf.manager import Configuration, ConfigProtocol

from batconf.source import SourceList
from batconf.sources.args import CliArgsConfig, Namespace
from batconf.sources.env import EnvConfig
from batconf.sources.file import FileConfig
from batconf.sources.dataclass import DataclassConfig


def get_config(
    # Known issue: https://github.com/python/mypy/issues/4536
    config_class: ConfigProtocol = GlobalConfig,  # type: ignore
    cli_args: Namespace = None,
    config_file: FileConfig = None,
    config_file_name: str = None,
    config_env: str = None,
) -> Configuration:

    # Build a prioritized config source list
    config_sources = [
        CliArgsConfig(cli_args) if cli_args else None,
        EnvConfig(),
        config_file if config_file else FileConfig(
            config_file_name, config_env=config_env
        ),
        DataclassConfig(config_class),
    ]

    source_list = SourceList(config_sources)

    return Configuration(source_list, config_class)
