"""
RemoveScaffold class:
    - Removes and deletes all framework related files
    and references, including harbinger.cfg section
"""

import configparser
import os
import shutil

from oslo_config import cfg
from oslo_log import log as logging

from harbinger import base

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class RemoveScaffold(base.Base):
    description = "removes and deletes all framework related " \
                  "files and references, including harbinger.cfg section"

    def get_description(self):
        return self.description

    def get_parser(self, prog_name):
        parser = super(RemoveScaffold, self).get_parser(prog_name)
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
        self.config = configparser.RawConfigParser()
        self.config.read(self.harbinger_cfg_path)

        self.delete_framework_section()
        self.delete_framework_directories()
        self.delete_venv_directories()
        self.delete_executor_file()
        LOG.info('---------------')
        LOG.info("Make sure to remove references to framework in Dockerfile")
        LOG.info('---------------')

    def delete_framework_section(self):
        LOG.info('Deleting harbinger.cfg %s section', self.app_args.framework)
        self.config.remove_section(self.app_args.framework)
        with open(self.harbinger_cfg_path, 'wb') as configfile:
            self.config.write(configfile)

    def delete_executor_file(self):
        LOG.info('Deleting %s framework executor file',
                 self.app_args.framework)
        try:
            os.remove(self.executor_path)
        except Exception:
            LOG.warning('File %s does not exist', self.executor_path)

    def delete_framework_directories(self):
        LOG.info('Deleting framework directory %s', self.app_args.framework)
        full_path = os.path.join(
            CONF.DEFAULT.files_dir, "frameworks", self.app_args.framework)
        try:
            shutil.rmtree(full_path)
        except Exception:
            LOG.warning("Directory %s does not exist", full_path)

    def delete_venv_directories(self):
        LOG.info('Deleting venvs directory %s', self.app_args.framework)
        full_path = os.path.join(
            CONF.DEFAULT.files_dir, "venvs", self.app_args.framework)
        try:
            shutil.rmtree(full_path)
        except Exception:
            LOG.warning("Directory %s does not exist", full_path)
