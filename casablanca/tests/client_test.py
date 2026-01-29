from unittest import TestCase
from unittest.mock import patch, Mock

from ..client import RabbitmqClient


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

    def test_read_one(t) -> None:
        with t.assertRaises(NotImplementedError):
            # TODO: implement read_one method
            t.rc.read_one('queue')
