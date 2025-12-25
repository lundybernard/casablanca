from __future__ import annotations

from dataclasses import dataclass


class RabbitmqClient:
    @dataclass
    class Config:
        hostname: str

    def __init__(self, hostname: str):
        self._hostname = hostname

    @classmethod
    def from_config(cls, cfg: RabbitmqClient.Config):
        return cls(hostname=cfg.hostname)
