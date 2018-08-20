"""
ListFrameworks class:
    - Lists all the frameworks that have been provided
    through the provided yaml file
"""

from harbinger import base
from harbinger.common.utils import Utils
from oslo_config import cfg
from oslo_log import log as logging
from prettytable import PrettyTable

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class ListFrameworks(base.Base):
    description = "lists all supported frameworks"

    def get_description(self):
        return self.description

    def get_parser(self, prog_name):
        parser = super(ListFrameworks, self).get_parser(prog_name)

        return parser

    def take_action(self, parsed_args):
        self.framework_tables = PrettyTable(["Frameworks"])
        self.supported_frameworks = Utils.get_supported_frameworks()
        self.log_frameworks(self.supported_frameworks)

    def log_frameworks(self, supported_frameworks):
        for key in supported_frameworks:
            self.framework_tables.add_row([key])
        print(self.framework_tables)
