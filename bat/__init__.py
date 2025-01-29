from dataclasses import dataclass

from .example import Config


@dataclass
class GlobalConfig:
    # example module with configuration dataclass
    example: Config
