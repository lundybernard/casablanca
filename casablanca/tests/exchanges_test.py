from unittest import TestCase
from unittest.mock import Mock, patch

from amqpstorm.management import ApiError

from ..exchanges import Exchange, ExchangeManager


SRC = 'casablanca.exchanges'


class ExchangesTests(TestCase):
    ExchangeManager: Mock

    def setUp(t) -> None:
        patches = [
            'ExchangeManager',
        ]
        for target in patches:
            patcher = patch(f'{SRC}.{target}', autospec=True)
            setattr(t, target, patcher.start())
            t.addCleanup(patcher.stop)

        t.name = '+name+'
        t.exchange_manager = t.ExchangeManager.return_value
        t.virtual_host = '/virtual/host/name/'
        t.exchange_type = '+fanout+'
        t.passive = True
        t.durable = True
        t.auto_delete = True
        t.arguments = {'arg0': 'v0', 'arg1': 'v1'}

        t.exchange = Exchange(
            name=t.name,
            exchange_manager=t.exchange_manager,
        )

    def test___init__(t) -> None:
        with t.subTest('defaults'):
            ret = Exchange(name=t.name, exchange_manager=t.exchange_manager)
            # required
            t.assertEqual(ret.name, t.name)
            t.assertEqual(ret._exchange_manager, t.exchange_manager)
            # defaults
            t.assertEqual(ret.virtual_host, '/')
            t.assertEqual(ret.exchange_type, 'fanout')
            t.assertIs(ret.passive, False)
            t.assertIs(ret.durable, False)
            t.assertIs(ret.arguments, None)

        with t.subTest('optional arguments'):
            ret = Exchange(
                name=t.name,
                exchange_manager=t.exchange_manager,
                virtual_host=t.virtual_host,
                exchange_type=t.exchange_type,
                passive=t.passive,
                durable=t.durable,
                auto_delete=t.auto_delete,
                arguments=t.arguments,
            )
            # required
            t.assertEqual(ret.name, t.name)
            t.assertEqual(ret._exchange_manager, t.exchange_manager)
            # options
            t.assertEqual(ret.virtual_host, t.virtual_host)
            t.assertEqual(ret.exchange_type, t.exchange_type)
            t.assertIs(ret.passive, t.passive)
            t.assertIs(ret.durable, t.durable)
            t.assertIs(ret.arguments, t.arguments)

    def test_declare(t) -> None:
        """Just passing the config through
        to the ExchangeManager's declare
        method
        """
        t.exchange.declare()
        t.exchange_manager.declare.assert_called_with(
            name=t.name,
            exchange_api=t.exchange_manager,
            virtual_host=t.virtual_host,
            exchange_type=t.exchange_type,
            passive=t.passive,
            durable=t.durrable,
            auto_delete=t.auto_delete,
            arguments=t.arguments,
        )

    def test_exists(t) -> None:
        """returns true if the exchange already exists on the rmq server"""
        with t.subTest('exchange already exists'):
            t.assertIs(t.exchange.exists, True)
            t.exchange_manager.get.assert_called_with(
                t.exchange.name,
                virtual_host=t.exchange.virtual_host,
            )

        with t.subTest('exchange does not exist'):
            """exchange_manager get method raises an ApiError if the exchange
            does not exist"""
            t.exchange_manager.get.side_effect = ApiError
            t.assertIs(False, t.exchange.exists)

    def test_delete(t) -> None:
        t.exchange.delete()
        t.exchange_manager.delete.assert_called_with(
            name=t.exchange.name,
            virtual_host=t.exchange.virtual_host,
        )
