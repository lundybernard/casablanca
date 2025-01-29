from unittest import TestCase
import subprocess

#from container_tests.docker_compose_fixture import DockerCompose

from project.tests.common_api_tests import CommonAPITest

'''
class DockerComposeFunctionalTests(TestCase, CommonAPITest):

    def setUp(self):
        self.service_address = 'http://0.0.0.0:5000/'
        self.dc = DockerCompose()
        self.dc.up()
        time.sleep(1)

    def tearDown(self):
        self.dc.down()
'''


class DockerComposeFunctionalTests(TestCase, CommonAPITest):

    def setUp(t):
        t.service_address = 'http://0.0.0.0:5000/'
        t.compose = subprocess.Popen(
            ['docker-compose', 'up'], stdout=subprocess.PIPE#, stderr=subprocess.PIPE
        )
        while True:
            line = t.compose.stdout.readline()
            if b'Debugger PIN' in line:
                break

    def tearDown(t):
        t.compose.kill()
