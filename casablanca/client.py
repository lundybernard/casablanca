from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

from pika import (
    BlockingConnection as _BlockingConnection,
    ConnectionParameters as _ConnectionParameters,
    PlainCredentials as _PlainCredentials,
)

from pika.adapters.blocking_connection import (
    BlockingChannel as _BlockingChannel,
)


from .manager import RabbitMQManager


class RabbitmqClient:
    @dataclass
    class Config:
        hostname: str = 'localhost'
        username: str = 'guest'
        password: str = 'guest'
        port: str | int = 5672
        adminport: str | int = 15672

    def __init__(
        self,
        host_name: str = 'localhost',
        username: str = 'guest',
        password: str = 'guest',
        port: int = 5672,
        admin_port: int = 15672,
    ) -> None:
        self.host_name = host_name
        self.username = username
        self.password = password
        self.admin_port = admin_port
        self.port = port

    @classmethod
    def from_config(cls, cfg: RabbitmqClient.Config):
        return cls(
            host_name=cfg.hostname,
            port=int(cfg.port),
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
        # to publish anything we need a channel
        self._channel.queue_declare(queue=queue)
        self._channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=message,
        )

    @cached_property
    def _channel(self) -> _BlockingChannel:
        return self._connection.channel()

    @cached_property
    def _connection(self) -> _BlockingConnection:
        # to get a channel we need a connection to the RMQ service
        return _BlockingConnection(self._connection_parameters)

    @property
    def _connection_parameters(self) -> _ConnectionParameters:
        """Pica connection parameters used to connect to the RMQ service"""
        params = _ConnectionParameters(
            host=self.host_name,
            port=self.port,
            credentials=self._credentials,
        )
        return params

    @property
    def _credentials(self) -> _PlainCredentials:
        return _PlainCredentials(
            username=self.username,
            password=self.password,
        )

    def read_one(self, queue: str) -> str:
        raise NotImplementedError('Read one method is not implemented')
