from .manager import ExchangeManager

from amqpstorm.management import ApiError


class Exchange:
    """Represents a single Exchange on the amqp server
    carries a reference to the ExchangeManager instance it uses
    to communicate with the server
    """

    def __init__(
        self,
        name: str,
        exchange_manager: ExchangeManager,
        virtual_host: str = '/',
        exchange_type: str = 'fanout',
        passive: bool = False,
        durable: bool = False,
        auto_delete: bool = False,
        arguments: dict | None = None,
    ) -> None:
        self.name = name
        self._exchange_manager = exchange_manager
        self.virtual_host = virtual_host
        self.exchange_type = exchange_type
        self.passive = passive
        self.durable = durable
        self.auto_delete = auto_delete
        self.arguments = arguments

    def declare(self):
        self._exchange_manager.declare(
            name=self.name,
            exchange_type=self.exchange_type,
            virtual_host=self.virtual_host,
            passive=self.passive,
            durable=self.durable,
            auto_delete=self.auto_delete,
            arguments=self.arguments,
        )
        assert self.exists

    @property
    def exists(self) -> bool:
        try:
            self._exchange_manager.get(
                self.name, virtual_host=self.virtual_host
            )
            return True
        except ApiError:
            return False

    def delete(self):
        self._exchange_manager.delete(
            name=self.name, virtual_host=self.virtual_host
        )
