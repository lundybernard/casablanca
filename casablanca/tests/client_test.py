from unittest import TestCase
from unittest.mock import patch

from ..client import RabbitmqClient


SRC = 'casablanca.client'


class RabbitmqClientTests(TestCase):
    def setUp(t):
        patches = [
            'RabbitMQManager',
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
        adminport = '7777777'
        username = 'user.name'
        password = 'pass.word'
        cfg = RabbitmqClient.Config(
            hostname=hostname,
            adminport=adminport,
            username=username,
            password=password,
        )
        rc = RabbitmqClient.from_config(cfg)

        t.assertEqual(rc.host_name, hostname)
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
        with t.assertRaises(NotImplementedError):
            # TODO: implement publish method
            t.rc.publish('message', 'queue')

    def test_read_one(t) -> None:
        with t.assertRaises(NotImplementedError):
            # TODO: implement read_one method
            t.rc.read_one('queue')
