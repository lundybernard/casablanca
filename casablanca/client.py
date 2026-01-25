from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

from .manager import RabbitMQManager


class RabbitmqClient:
    @dataclass
    class Config:
        hostname: str = 'localhost'
        username: str = 'guest'
        password: str = 'guest'
        adminport: str | int = 15672

    def __init__(
        self,
        host_name: str = 'localhost',
        username: str = 'guest',
        password: str = 'guest',
        admin_port: int = 15672,
    ) -> None:
        self.host_name = host_name
        self.username = username
        self.password = password
        self.admin_port = admin_port

    @classmethod
    def from_config(cls, cfg: RabbitmqClient.Config):
        return cls(
            host_name=cfg.hostname,
            username=cfg.username,
            password=cfg.password,
            admin_port=int(cfg.adminport),
        )

    @cached_property
    def manager(self) -> RabbitMQManager:
        return RabbitMQManager(
            host_name=self.host_name,
            admin_port=self.admin_port,
            username=self.username,
            password=self.password,
        )

        raise NotImplementedError('Manager property is not implemented')

    def publish(self, message: str, queue: str) -> None:
        raise NotImplementedError('Publish method is not implemented')

    def read_one(self, queue: str) -> str:
        raise NotImplementedError('Read one method is not implemented')
