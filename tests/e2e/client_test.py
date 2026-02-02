from typing import Iterator

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
def rabbitmq(request: FixtureRequest) -> Iterator[RabbitMQInfo]:
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


@mark.usefixtures('rabbitmq')
class RabbitmqClientTests(TestCase):
    @fixture(autouse=True)
    def _wire_client_from_container_info(t, rabbitmq: RabbitMQInfo):
        t.test_queue = 'tests.e2e.RabbitmqClientTests'
        cfg = get_config().rabbitmq

        cfg.hostname = rabbitmq.host
        cfg.port = rabbitmq.amqp_port
        cfg.adminport = rabbitmq.mgmt_port

        t.rc = RabbitmqClient.from_config(cfg)

    def test_server_online_check(t):
        assert t.rc.manager.online is True

    def test_publish_message(t):
        msg = b'Hello World!'
        t.rc.publish(msg, t.test_queue)

        ret = t.rc.read_one(queue=t.test_queue)
        t.assertEqual(ret, msg)

    def test_read_message(t):
        message = 'why hello there'
        t.rc.publish(message, queue=t.test_queue)
        ret = t.rc.read_one(queue=t.test_queue)
        t.assertEqual(ret, bytes(message, 'utf-8'))

    def test_publisher(t):
        """The publisher is used to send messages
        to the exchange it is bound to.  It is long-lived and used to send
        multiple messages over time.
        """
        prefix = 'tests.e2e.RabbitmqClientTests'
        exchange = f'{prefix}.exhange'
        queue = f'{prefix}.queue'
        route = 'test_publisher'

        # Before we can publish anything we need to declare an exchange
        # and bind it to a queue, so we can check that the messages we publish
        # are delivered.

        t.rc.exchanges[exchange].declare()  # cache exchanges on the client
        # TODO: wrap the direct channel manipulation in an interface
        t.rc._channel.queue_declare(queue)
        t.rc._channel.queue_bind(
            queue=queue,
            exchange=exchange,
            routing_key=route,
        )

        publisher = t.rc.new_publisher(
            exchange=exchange,
            routing_key=route,
        )
        publisher.send('hello world')
        publisher.send('hello dave')

        assert t.rc.get_queue_length(queue) == 2

    def test_creating_an_exchange(t):
        """create named exchanges and cache them on the rmq client"""
        exchange_id = 'test.e2e.exchange'
        exchange_manager = t.rc.manager.exchange

        # make sure we are not duplicating the exchange
        assert exchange_manager.list_exchanges(name=exchange_id) == []

        # create a new exchange in the cache
        exchange = t.rc.exchanges[exchange_id]
        # send the command to the rmq service to create it
        exchange.declare()

        assert t.rc.exchanges[exchange_id].exists is True
        exchange_list = exchange_manager.list_exchanges(name=exchange_id)
        assert len(exchange_list) == 1
        assert exchange_list[0]['name'] == exchange_id


class ConfigTests(TestCase):
    """Test configuration values used for e2e and other source-code tests"""

    def test_config_values(t):
        cfg = get_config()
        t.assertEqual(cfg.rabbitmq.hostname, 'localhost')
