from unittest import TestCase
from unittest.mock import patch, Mock

from ..client import RabbitmqClient, ReadOneHandler


SRC = 'casablanca.client'


class RabbitmqClientTests(TestCase):
    RabbitMQManager: Mock
    _BlockingConnection: Mock
    _PlainCredentials: Mock
    _ConnectionParameters: Mock

    def setUp(t):
        patches = [
            'RabbitMQManager',
            '_BlockingConnection',
            '_PlainCredentials',
            '_ConnectionParameters',
        ]
        for target in patches:
            patcher = patch(f'{SRC}.{target}', autospec=True)
            setattr(t, target, patcher.start())
            t.addCleanup(patcher.stop)

        t.rc = RabbitmqClient(host_name='unit.test.rmq')

    def test___init__(t):
        rc = RabbitmqClient()
        with t.subTest('default values'):
            t.assertEqual(rc.host_name, 'localhost')
            t.assertEqual(rc.admin_port, 15672)
            t.assertEqual(rc.username, 'guest')
            t.assertEqual(rc.password, 'guest')
        with t.subTest('parameters'):
            rc = RabbitmqClient(
                host_name='hostname',
                admin_port=7777777,
                username='username',
                password='password',
            )
            t.assertEqual(rc.host_name, 'hostname')
            t.assertEqual(rc.admin_port, 7777777)
            t.assertEqual(rc.username, 'username')
            t.assertEqual(rc.password, 'password')

    def test_from_config(t):
        hostname = 'some.host.name'
        port = '555'
        adminport = '7777777'
        username = 'user.name'
        password = 'pass.word'
        cfg = RabbitmqClient.Config(
            hostname=hostname,
            port=port,
            adminport=adminport,
            username=username,
            password=password,
        )
        rc = RabbitmqClient.from_config(cfg)

        t.assertEqual(rc.host_name, hostname)
        t.assertEqual(rc.port, int(port))
        t.assertEqual(rc.admin_port, int(adminport))
        t.assertEqual(rc.username, username)
        t.assertEqual(rc.password, password)

    def test_exchanges(t):
        """referencing an exchange in the cache creates and returns a new
        instance
        """
        e1 = t.rc.exchanges['E1']
        e2 = t.rc.exchanges['E2']
        t.assertEqual(e1.name, 'E1')
        t.assertEqual(e2.name, 'E2')
        t.assertDictEqual(t.rabbit.exchanges, {'E1': e1, 'E2': e2})

    def test_exchange_manager(t):
        t.assertIs(t.rc.exchange_manager, t.rc.manager.exchange)

    def test_manager(t):
        t.assertIs(t.rc.manager, t.RabbitMQManager.return_value)
        t.RabbitMQManager.assert_called_with(
            host_name=t.rc.host_name,
            admin_port=t.rc.admin_port,
            username=t.rc.username,
            password=t.rc.password,
        )

    def test_publish(t) -> None:
        message = '+message+'
        queue = '+queue+'
        t.rc.publish(message, queue)
        # declare the queue each time, to be sure it exists
        t.rc._channel.queue_declare.assert_called_with(queue=queue)
        t.rc._channel.basic_publish.assert_called_with(
            exchange='',
            routing_key=queue,
            body=message,
        )

    def test__channel(t) -> None:
        channel = t.rc._channel
        t.assertIs(channel, t.rc._connection.channel.return_value)

    def test__connection(t) -> None:
        t.assertIs(t.rc._connection, t._BlockingConnection.return_value)
        t._BlockingConnection.assert_called_with(t.rc._connection_parameters)

    def test__connection_parameters(t) -> None:
        t.assertIs(
            t.rc._connection_parameters,
            t._ConnectionParameters.return_value,
        )
        t._ConnectionParameters.assert_called_with(
            host=t.rc.host_name,
            port=t.rc.port,
            credentials=t.rc._credentials,
        )

    def test__credentials(t) -> None:
        t.assertIs(t.rc._credentials, t._PlainCredentials.return_value)
        t._PlainCredentials.assert_called_with(
            username=t.rc.username,
            password=t.rc.password,
        )

    @patch(f'{SRC}.ReadOneHandler', autospe=True)
    def test_read_one(t, ReadOneHandler: Mock) -> None:
        queue = 'unittest_queue'
        ret = t.rc.read_one(queue)

        handler = ReadOneHandler.return_value
        channel = t.rc._channel
        channel.basic_consume.assert_called_with(
            queue=queue,
            auto_ack=True,
            on_message_callback=handler,
        )
        channel.start_consuming.assert_called_once()
        t.assertIs(ret, handler.message)


class ReadOneHandlerTests(TestCase):
    @patch(f'{SRC}._BlockingChannel', autospec=True)
    def test___call__(t, _BlockingChannel: Mock):
        channel = _BlockingChannel.return_value
        message = b'+incomming-message+'
        read_one_handler = ReadOneHandler()
        read_one_handler(
            channel=channel,
            method=None,
            properties=None,
            body=message,
        )
        channel.stop_consuming.assert_called_once()
        channel.close.assert_called_once()
        t.assertIs(message, read_one_handler.message)

    def test_message(t):
        message = '+cached_message+'
        read_one_handler = ReadOneHandler()
        t.assertIsNone(read_one_handler.message)
        read_one_handler.message = message
        t.assertEqual(message, read_one_handler.message)
