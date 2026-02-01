from __future__ import annotations
from typing import Generic, TypeVar, Callable

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


from .manager import RabbitMQManager, ExchangeManager
from .exchanges import Exchange


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
    def exchanges(self) -> dict[str, Exchange]:
        """We need a factory method that encapsulates this instances
        exchange_manager, so that it can be passed to the new Exchange object
        when it is created"""
        return _ExchangeCache(_ExchangeFactory(self.exchange_manager))

    @property
    def exchange_manager(self) -> ExchangeManager:
        return self.manager.exchange

    @cached_property
    def manager(self) -> RabbitMQManager:
        return RabbitMQManager(
            host_name=self.host_name,
            admin_port=self.admin_port,
            username=self.username,
            password=self.password,
        )

    def publish(self, message: str, queue: str) -> None:
        # to publish anything we need a channel
        self._channel.queue_declare(queue=queue)
        self._channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=message,
        )

    def read_one(self, queue: str) -> bytes | None:
        """Read a single message from a queue
        this blocks while awaiting a message,
        and is useful for testing and debugging.
        """
        handler = ReadOneHandler()
        # Listen for incoming messages on a specific queue
        self._channel.basic_consume(
            queue=queue,
            auto_ack=True,
            on_message_callback=handler,
        )
        # This is a blocking operation
        self._channel.start_consuming()
        return handler.message

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


class ReadOneHandler:
    """on_message_callback handler
    waits for a single message, records it, then stops and closes the channel
    """

    def __init__(self):
        self._message = None

    def __call__(
        self,
        channel: _BlockingChannel,
        method,
        properties,
        body: bytes,
    ) -> None:
        self._message = body
        channel.stop_consuming()
        channel.close()

    @cached_property
    def message(self) -> bytes | None:
        return self._message


class _ExchangeFactory:
    """Key-aware factory for Exchange objects."""

    def __init__(self, exchange_manager: ExchangeManager) -> None:
        self._exchange_manager = exchange_manager

    def __call__(self, name: str) -> Exchange:
        return Exchange(name=name, exchange_manager=self._exchange_manager)


class _ExchangeCache(dict[str, Exchange]):
    """Dict-like cache that creates Exchange objects on demand."""

    def __init__(self, factory: Callable[[str], Exchange]) -> None:
        super().__init__()
        self._factory = factory

    def __missing__(self, key: str) -> Exchange:
        ex = self._factory(key)
        self[key] = ex
        return ex
