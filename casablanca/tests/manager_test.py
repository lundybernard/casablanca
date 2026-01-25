from unittest import TestCase
from unittest.mock import patch

from ..manager import RabbitMQManager


SRC = 'casablanca.manager'


class RabbitMQManagerTests(TestCase):
    def setUp(t):
        patches = [
            '_ManagementApi',
        ]
        for target in patches:
            patcher = patch(f'{SRC}.{target}', autospec=True)
            setattr(t, target, patcher.start())
            t.addCleanup(patcher.stop)

        # t.management_api = create_autospec(ManagementApi, instance=True)
        # t.ManagementApi.return_value = t.management_api
        t.management_api = t._ManagementApi(
            api_url='/',
            username='usr',
            password='pwd',
        )

        t.rmqm = RabbitMQManager()

    def test___init__(t):
        with t.subTest('default values'):
            rmqm = RabbitMQManager()

            t.assertEqual(rmqm.vhost, '/')
            t.assertEqual(rmqm.host_name, 'localhost')
            t.assertEqual(rmqm.admin_port, 15627)
            t.assertEqual(rmqm.username, 'guest')
            t.assertEqual(rmqm.password, 'guest')

        with t.subTest('parameters'):
            rmqm = RabbitMQManager(
                vhost='vhost',
                host_name='host_name',
                admin_port=7777777,
                username='username',
                password='password',
            )
            t.assertEqual(rmqm.vhost, 'vhost')
            t.assertEqual(rmqm.host_name, 'host_name')
            t.assertEqual(rmqm.admin_port, 7777777)
            t.assertEqual(rmqm.username, 'username')
            t.assertEqual(rmqm.password, 'password')

    def test_online(t):
        t.management_api.aliveness_test.return_value = {'status': 'ok'}
        t.assertTrue(t.rmqm.online)
        t.management_api.aliveness_test.assert_called_with(t.rmqm.vhost)

        t.management_api.aliveness_test.return_value = {'status': 'not ok'}
        t.assertFalse(t.rmqm.online)

    def test_management_api(t):
        mgr = RabbitMQManager()
        t.assertIs(mgr._management_api, t._ManagementApi.return_value)
        t._ManagementApi.assert_called_with(
            api_url=mgr._api_url,
            username=mgr.username,
            password=mgr.password,
        )

    def test__api_url(t):
        t.assertEqual(
            t.rmqm._api_url,
            'http://localhost:15627',
        )
