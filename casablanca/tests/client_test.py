from unittest import TestCase

from ..client import RabbitmqClient


class RabbitmqClientTests(TestCase):
    def test___init__(t):
        rmq = RabbitmqClient(hostname='xxx')

        t.assertEqual(rmq._hostname, 'xxx')

    def test_from_config(t):
        hostname = 'some.host.name'
        cfg = RabbitmqClient.Config(hostname=hostname)
        rmq = RabbitmqClient.from_config(cfg)

        t.assertEqual(rmq._hostname, hostname)
