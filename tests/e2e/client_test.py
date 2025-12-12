from dataclasses import dataclass
from base64 import b64encode
from urllib.request import Request, urlopen

import pytest

from testcontainers.rabbitmq import RabbitMqContainer
from testcontainers.core.wait_strategies import HttpWaitStrategy


@dataclass(frozen=True)
class RabbitMQInfo:
    host: str
    amqp_port: int
    mgmt_port: int
    amqp_url: str
    mgmt_url: str


@pytest.fixture(scope='session')
def rabbitmq(request: pytest.FixtureRequest) -> RabbitmQInfo:

    with RabbitMqContainer(
        "rabbitmq:3-management"
    ).with_exposed_ports(5672, 15672) as rmq:
        rmq.waiting_for(
            HttpWaitStrategy(15672, path="/api/overview").for_status_code(401)
        )

        host = rmq.get_container_host_ip()
        amqp_port = int(rmq.get_exposed_port(5672))
        mgmt_port = int(rmq.get_exposed_port(15672))

        info = RabbitMQInfo(
            host=host,
            amqp_port=amqp_port,
            mgmt_port=mgmt_port,
            amqp_url=f"amqp://guest:guest@{host}:{amqp_port}/",
            mgmt_url=f"http://{host}:{mgmt_port}",
        )

        yield info


def _mgmt_overview_is_ready(mgmt_url: str) -> bool:
    auth = b64encode(b"guest:guest").decode("ascii")
    req = Request(
        mgmt_url.rstrip("/") + "/api/overview",
        headers={"Authorization": f"Basic {auth}"},
    )
    try:
        with urlopen(req, timeout=2) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


@mark.usefixtures("rabbitmq")
class FeatureTests:

    def test_server_online_check(t, rmq_info: RabbitMQInfo):
        cfg = get_config().rabbitmq
        t.rc = RabbitmqClient.from_config(cfg)

        assert t.rc.manager.online is True
