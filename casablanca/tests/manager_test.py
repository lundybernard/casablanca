from unittest import TestCase
from unittest.mock import patch, Mock

from ..manager import RabbitMQManager, ExchangeManager, _ApiError, ApiError


SRC = 'casablanca.manager'


class RabbitMQManagerTests(TestCase):
    _ManagementApi: Mock

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


class ExchangeManagerTests(TestCase):
    _ManagementApi: Mock

    def setUp(t) -> None:
        patches = [
            '_ManagementApi',
        ]
        for target in patches:
            patcher = patch(f'{SRC}.{target}', autospec=True)
            setattr(t, target, patcher.start())
            t.addCleanup(patcher.stop)

        t.management_api = t._ManagementApi.return_value
        t.exchange_api = t.management_api.exchange
        t.em = ExchangeManager(t.management_api.exchange)

    def test___init__(t) -> None:
        ret = ExchangeManager(exchange_api=t.exchange_api)
        t.assertIsInstance(ret, ExchangeManager)

    def test_get(t) -> None:
        """Call the exchange api to return an exchange handle"""
        exchange_name = '+exchange-name+'
        vhost = '/virtual/host/'

        ret = t.em.get(exchange_name=exchange_name, virtual_host=vhost)

        t.exchange_api.get.assert_called_with(
            exchange=exchange_name, virtual_host=vhost
        )
        t.assertIs(ret, t.exchange_api.get.return_value)

        with t.subTest('raises ApiError'):
            t.exchange_api.get.side_effect = _ApiError
            with t.assertRaises(ApiError):
                t.em.get(exchange_name=exchange_name, virtual_host=vhost)

    def test_list_exchanges(t) -> None:
        """get a list of all exchanges from the rmq server"""
        with t.subTest('default parameters'):
            ret = t.em.list_exchanges()
            t.assertIs(ret, t.exchange_api.list.return_value)
            t.exchange_api.list.assert_called_with(
                virtual_host='/',
                name=None,
                show_all=False,
                page_size=100,
                use_regex=False,
            )

        with t.subTest('optional parameters'):
            vhost = '/virtual/host'
            name = '+specific-name+'
            show_all = True
            page_size = 999
            use_regex = True

            ret = t.em.list_exchanges(
                virtual_host=vhost,
                name=name,
                show_all=show_all,
                page_size=page_size,
                use_regex=use_regex,
            )
            t.exchange_api.list.assert_called_with(
                virtual_host=vhost,
                name=name,
                show_all=show_all,
                page_size=page_size,
                use_regex=use_regex,
            )
            t.assertIs(ret, t.exchange_api.list.return_value)
