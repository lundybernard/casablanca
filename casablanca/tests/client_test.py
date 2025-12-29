from unittest import TestCase

from ..client import RabbitmqClient


class RabbitmqClientTests(TestCase):
    def setUp(t):
        t.rc = RabbitmqClient(hostname='unit.test.rmq')

    def test___init__(t):
        rc = RabbitmqClient(hostname='xxx')

        t.assertEqual(rc._hostname, 'xxx')

    def test_from_config(t):
        hostname = 'some.host.name'
        cfg = RabbitmqClient.Config(hostname=hostname)
        rc = RabbitmqClient.from_config(cfg)

        t.assertEqual(rc._hostname, hostname)

    def test_manager(t):
        with t.assertRaises(NotImplementedError):
            # TODO: implement manager property
            t.assertIs(t.rc.manager, None)

    def test_publish(t) -> None:
        with t.assertRaises(NotImplementedError):
            # TODO: implement publish method
            t.rc.publish('message', 'queue')

    def test_read_one(t) -> None:
        with t.assertRaises(NotImplementedError):
            # TODO: implement read_one method
            t.rc.read_one('queue')
