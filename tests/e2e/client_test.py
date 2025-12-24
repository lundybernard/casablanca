from unittest import TestCase

from dataclasses import dataclass
from base64 import b64encode
from urllib.request import Request, urlopen

from casablanca import RabbitmqClient
from casablanca.conf import get_config

from pytest import mark, fixture, FixtureRequest

from testcontainers.rabbitmq import RabbitMqContainer
from testcontainers.core.wait_strategies import HttpWaitStrategy


@dataclass(frozen=True)
class RabbitMQInfo:
    host: str
    amqp_port: int
    mgmt_port: int
    amqp_url: str
    mgmt_url: str


@fixture(scope='session')
def rabbitmq(request: FixtureRequest) -> RabbitMQInfo:
    with RabbitMqContainer('rabbitmq:3-management').with_exposed_ports(
        5672, 15672
    ) as rmq:
        rmq.waiting_for(
            HttpWaitStrategy(15672, path='/api/overview').for_status_code(401)
        )

        host = rmq.get_container_host_ip()
        amqp_port = int(rmq.get_exposed_port(5672))
        mgmt_port = int(rmq.get_exposed_port(15672))

        info = RabbitMQInfo(
            host=host,
            amqp_port=amqp_port,
            mgmt_port=mgmt_port,
            amqp_url=f'amqp://guest:guest@{host}:{amqp_port}',
            mgmt_url=f'http://{host}:{mgmt_port}',
        )

        yield info


def _mgmt_overview_is_ready(mgmt_url: str) -> bool:
    auth = b64encode(b'guest:guest').decode('ascii')
    req = Request(
        f'{mgmt_url}/api/overview',
        headers={'Authorization': f'Basic {auth}'},
    )
    try:
        with urlopen(req, timeout=2) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


@mark.usefixtures('rabbitmq')
class FeatureTests(TestCase):
    def setUp(t):
        t.test_queue = 'tests.e2e.FeatureTests'
        cfg = get_config().rabbitmq
        t.rc = RabbitmqClient.from_config(cfg)

    def test_server_online_check(t):
        assert t.rc.manager.online is True

    def test_publish_message(t):
        msg = 'Hello World!'

        t.rc.publish(msg, t.test_queue)

        ret = t.rc.read_one(queue=t.test_queue)
        t.assertEqual(ret, msg)

    def test_read_message(t):
        message = 'why hello there'
        r.rc.publish(message, queue=t.test_queue)
        ret = t.rc.read_one(queue=t.test_queue)
        t.assertEqual(ret, bytes(message, 'utf-8'))


class ConfigTests(TestCase):
    """Test configuration values used for e2e and other source-code tests"""

    def test_config_values(t):
        cfg = get_config()
        t.assertEqual(cfg.rabbitmq.hostname, 'localhost')
