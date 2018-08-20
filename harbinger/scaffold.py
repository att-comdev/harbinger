"""
Scaffold class:
    - creates boiler plate framework file and
    harbinger.cfg option for the framework
"""

import ConfigParser
import os

from harbinger import base
from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class Scaffold(base.Base):
    description = "creates boiler plate framework file and " \
                  "harbinger.cfg option for framework"

    def get_description(self):
        return self.description

    def get_parser(self, prog_name):
        parser = super(Scaffold, self).get_parser(prog_name)
        parser.add_argument('framework',
                            metavar='<framework name>',
                            default='',
                            help=('Lists the tests available '
                                  'for the specified framework'),
                            )

        return parser

    def take_action(self, parsed_args):
        self.app_args.framework = parsed_args.framework
        self.app_args.framework_file = parsed_args.framework + ".py"
        self.executor_path = os.path.join(
            os.path.dirname(__file__), "executors",
            self.app_args.framework_file)
        self.harbinger_cfg_path = os.path.join(os.path.dirname(__file__),
                                               "etc/harbinger.cfg")
        self.config = ConfigParser.RawConfigParser()
        self.config.read(self.harbinger_cfg_path)

        self.add_framework_section()
        self.create_framework_directories()
        self.create_venv_directories()
        self.create_executor_file()

    def add_framework_section(self):
        LOG.info('Adding harbinger.cfg %s section', self.app_args.framework)
        try:
            self.config.add_section(self.app_args.framework)
            with open(self.harbinger_cfg_path, 'wb') as configfile:
                self.config.write(configfile)
        except Exception:
            LOG.warning("Section %s already exists", self.app_args.framework)

    def create_executor_file(self):
        LOG.info('Creating %s framework executor file',
                 self.app_args.framework)
        open(self.executor_path, 'a').close()

    def create_framework_directories(self):
        LOG.info('Creating framework directory %s', self.app_args.framework)
        full_path = os.path.join(
            CONF.DEFAULT.files_dir, "frameworks",
            self.app_args.framework, self.app_args.framework)
        try:
            os.makedirs(full_path)
        except Exception:
            LOG.warning("Directory %s already exists", full_path)

    def create_venv_directories(self):
        LOG.info('Creating venvs directory %s', self.app_args.framework)
        full_path = os.path.join(
            CONF.DEFAULT.files_dir, "venvs",
            self.app_args.framework)
        try:
            os.makedirs(full_path)
        except Exception:
            LOG.warning("Directory %s already exists", full_path)
