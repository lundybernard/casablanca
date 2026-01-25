from functools import cached_property

from amqpstorm.management import ManagementApi as _ManagementApi


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
