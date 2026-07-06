"""Integration tests for the RabbitmqClient public contract.

Real internal collaborators (Publisher, Exchange, ExchangeManager,
RabbitMQManager) are wired together; only the vendor seams are stubbed
(ADR 08, as amended): ``casablanca.client._BlockingConnection`` and
``casablanca.manager._ManagementApi``, patched with autospec.

Vendor behaviour the stubs assume (e.g. ``start_consuming`` delivering
to the registered callback) is demonstrated for real by ``tests/e2e``.
"""

from unittest import TestCase
from unittest.mock import Mock, patch

from casablanca.client import Publisher, RabbitmqClient
from casablanca.exchanges import Exchange
from casablanca.manager import ExchangeManager


VENDOR_SEAMS = (
    'casablanca.client._BlockingConnection',
    'casablanca.manager._ManagementApi',
)


class RabbitmqClientTests(TestCase):
    _BlockingConnection: Mock
    _ManagementApi: Mock

    def setUp(t) -> None:
        for target in VENDOR_SEAMS:
            name = target.rsplit('.', 1)[-1]
            patcher = patch(target, autospec=True)
            setattr(t, name, patcher.start())
            t.addCleanup(patcher.stop)

        t.channel = t._BlockingConnection.return_value.channel.return_value
        t.rc = RabbitmqClient(
            # Default: host_name='localhost',
            # Default: username='guest',
            # Default: password='guest',
            # Default: port=5672,
            # Default: admin_port=15672,
        )

    def test_from_config(t) -> None:
        """A config-built client opens its vendor connection against the
        configured endpoint, through the real ConnectionParameters chain.
        """
        cfg = RabbitmqClient.Config(
            hostname='rmq.example',
            port='5673',
            adminport='15673',
            username='+user+',
            password='+pass+',
        )
        rc = RabbitmqClient.from_config(cfg)

        rc.publish('+message+', queue='+queue+')  # forces the connection

        params = t._BlockingConnection.call_args.args[0]
        t.assertEqual(params.host, 'rmq.example')
        t.assertEqual(params.port, 5673)
        t.assertEqual(params.credentials.username, '+user+')
        t.assertEqual(params.credentials.password, '+pass+')

    def test_publish(t) -> None:
        t.rc.publish('+message+', queue='+queue+')

        t.channel.queue_declare.assert_called_with(queue='+queue+')
        t.channel.basic_publish.assert_called_with(
            exchange='',
            routing_key='+queue+',
            body='+message+',
        )

    def test_read_one(t) -> None:
        """The real ReadOneHandler receives the delivery, stops the
        channel, and the body comes back as the return value.
        """

        def deliver() -> None:
            handler = t.channel.basic_consume.call_args.kwargs[
                'on_message_callback'
            ]
            handler(t.channel, Mock(), Mock(), b'+body+')

        t.channel.start_consuming.side_effect = deliver

        ret = t.rc.read_one('+queue+')

        t.assertEqual(ret, b'+body+')
        t.channel.stop_consuming.assert_called_once()
        t.channel.close.assert_called_once()

    def test_get_queue_length(t) -> None:
        t.channel.queue_declare.return_value.method.message_count = 3

        ret = t.rc.get_queue_length('+queue+')

        t.assertEqual(ret, 3)
        t.channel.queue_declare.assert_called_with(
            queue='+queue+', passive=True
        )

    def test_new_publisher(t) -> None:
        """The real Publisher shares the client's channel and publishes
        to its bound exchange/routing_key pair.
        """
        publisher = t.rc.new_publisher(
            exchange='+exchange+', routing_key='+routing_key+'
        )
        t.assertIsInstance(publisher, Publisher)

        publisher.send('+message+')

        t.channel.basic_publish.assert_called_with(
            exchange='+exchange+',
            routing_key='+routing_key+',
            body='+message+',
        )

    def test_exchanges(t) -> None:
        """Exchange objects from the cache drive the management API
        through the real ExchangeManager wrapper.
        """
        exchange_api = t._ManagementApi.return_value.exchange

        with t.subTest('cache creates and caches'):
            ex = t.rc.exchanges['+exchange+']
            t.assertIsInstance(ex, Exchange)
            t.assertIs(t.rc.exchanges['+exchange+'], ex)

        with t.subTest('declare'):
            ex.declare()
            exchange_api.declare.assert_called_with(
                exchange='+exchange+',
                exchange_type='fanout',
                virtual_host='/',
                passive=False,
                durable=False,
                auto_delete=False,
                internal=False,
                arguments=None,
            )

        with t.subTest('delete'):
            ex.delete()
            exchange_api.delete.assert_called_with(
                exchange='+exchange+', virtual_host='/'
            )

    def test_exchange_manager(t) -> None:
        t.assertIsInstance(t.rc.exchange_manager, ExchangeManager)

    def test_manager(t) -> None:
        api = t._ManagementApi.return_value
        api.aliveness_test.return_value = {'status': 'ok'}

        with t.subTest('api wiring'):
            t.assertTrue(t.rc.manager.online)
            t._ManagementApi.assert_called_with(
                api_url='http://localhost:15672',
                username='guest',
                password='guest',
            )
            api.aliveness_test.assert_called_with('/')

        with t.subTest('offline'):
            api.aliveness_test.return_value = {'status': 'failed'}
            t.assertFalse(t.rc.manager.online)
