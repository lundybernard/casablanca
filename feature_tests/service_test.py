from unittest import TestCase

PT_SVC_ADDR = 'http://0.0.0.0:5000/'
# PT_SVC_ADDR = 'http://127.0.0.1/project'

from casablanca.tests.common_api_tests import CommonAPITest


RMQ_HOST = '0.0.0.0'
RMQ_PORT = 5672


class ServiceFunctionalTest(TestCase, CommonAPITest):
    def setUp(self):
        self.service_address = PT_SVC_ADDR


def test_rabbitmq_service_up(rabbitmq_host, rabbitmq_port):
    """
    Test to ensure the RabbitMQ service is running by attempting to create a connection.

    This assumes RabbitMQ is running and accessible locally either via Docker
    or a standalone service on the specified host and port.
    """
    # First, check if the port is open and service is listening
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(5)  # Timeout after 5 seconds
        result = sock.connect_ex((rabbitmq_host, rabbitmq_port))
        # Assert that the port is open
        # result == 0 indicates successful connection
        assert (
            result == 0,
            f'RabbitMQ is not accessible at {RMQ_HOST}:{RMQ_PORT}',
        )

    # Next, attempt to connect using pika to verify RabbitMQ is operational
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RMQ_HOST, port=RMQ_PORT)
        )
        connection.close()  # If connected successfully, close it
    except Exception as e:
        pytest.fail(f'RabbitMQ service is not operational: {e}')
