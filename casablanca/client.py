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

    @property
    def manager(self):
        raise NotImplementedError("Manager property is not implemented")

    def publish(self, message: str, queue: str) -> None:
        raise NotImplementedError("Publish method is not implemented")

    def read_one(self, queue: str) -> str:
        raise NotImplementedError("Read one method is not implemented")
