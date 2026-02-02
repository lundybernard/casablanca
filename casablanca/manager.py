from typing import Protocol
from functools import cached_property

from amqpstorm.management import ManagementApi as _ManagementApi
from amqpstorm.management.exception import ApiError as _ApiError


class RabbitMQManager:
    def __init__(
        self,
        vhost: str = '/',
        host_name: str = 'localhost',
        admin_port: int = 15627,
        username: str = 'guest',
        password: str = 'guest',
    ) -> None:
        self.vhost = vhost
        self.host_name = host_name
        self.admin_port = admin_port
        self.username = username
        self.password = password

    @property
    def online(self) -> bool:
        ret = self._management_api.aliveness_test(self.vhost)
        if ret['status'] == 'ok':
            return True
        return False

    @property
    def exchange(self) -> ExchangeManagerProto:
        # Expose the exchange manager from the management api
        return ExchangeManager(self._management_api.exchange)

    @cached_property
    def _management_api(self) -> _ManagementApi:
        return _ManagementApi(
            api_url=self._api_url,
            username=self.username,
            password=self.password,
        )

    @cached_property
    def _api_url(self):
        return f'http://{self.host_name}:{self.admin_port}'


class ExchangeManagerProto(Protocol):
    def get(self, exchange: str, virtual_host: str) -> dict: ...
    def list(
        self,
        virtual_host: str,
        name: str,
        show_all: bool,
        page_size: int,
        use_regex: bool,
    ) -> list[dict]: ...


class ExchangeManager:
    """Wrapper class for the amqp exchange management API"""

    def __init__(self, exchange_api: ExchangeManagerProto):
        self._exchange_api = exchange_api

    def get(self, exchange_name: str, virtual_host: str) -> dict:
        try:
            return self._exchange_api.get(
                exchange=exchange_name, virtual_host=virtual_host
            )
        except _ApiError as e:
            raise ApiError(e)

    def list_exchanges(
        self,
        virtual_host: str = '/',
        name: str | None = None,
        show_all: bool = False,
        page_size: int = 100,
        use_regex: bool = False,
    ) -> list[dict]:
        return self._exchange_api.list(
            virtual_host=virtual_host,
            name=name,
            show_all=show_all,
            page_size=page_size,
            use_regex=use_regex,
        )


class ApiError(Exception): ...
