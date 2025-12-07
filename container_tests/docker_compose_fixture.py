from inspect import getdoc
from docopt import docopt
import time

from compose.cli.main import TopLevelCommand, project_from_options


def default_opts(self, command):
    '''given a docker-compose command
    return its default options
    '''
    cmd_help = getdoc(getattr(TopLevelCommand, command))
    return docopt(cmd_help, [])


class DockerCompose(object):

    def __init__(self, path='./'):
        path = './'  # Path to docker-compose directory
        self.options = {
            "--file": ['docker-compose.dev.yaml', ],
            "--no-deps": False,
            "--abort-on-container-exit": False,
            "SERVICE": "",
            "--remove-orphans": False,
            "--no-recreate": True,
            "--force-recreate": False,
            "--build": False,
            '--no-build': False,
            '--no-color': False,
            "--rmi": "none",
            "--volumes": "",
            "--follow": False,
            "--timestamps": False,
            "--tail": "all",
            "-d": True,
            '--always-recreate-deps': False,
            '--scale': []
        }

        self.project = project_from_options(path, self.options)
        self.cli = TopLevelCommand(self.project)

    def up(self, **kwargs):
        self.cli.up(self.options)
        time.sleep(1)  # wait for the server to be ready

    def down(self):
        self.cli.down(self.options)
