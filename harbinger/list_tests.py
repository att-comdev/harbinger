"""
ListTests class:
    - Lists all the available tests in the framework provided
    through an argument --framework-name
"""

import os

from harbinger import base
from oslo_config import cfg
from oslo_log import log as logging
from prettytable import PrettyTable

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class ListTests(base.Base):
    description = "lists the tests for the framework provided"

    def get_description(self):
        return self.description

    def get_parser(self, prog_name):
        parser = super(ListTests, self).get_parser(prog_name)
        parser.add_argument('framework',
                            metavar='<framework name>',
                            default='',
                            help=('Lists the tests available '
                                  'for the specified framework'),
                            )

        return parser

    def take_action(self, parsed_args):
        LOG.info('%s tests:\n', parsed_args.framework)

        self.app_args.framework = parsed_args.framework
        self.tests_format = CONF[self.app_args.framework].tests_format

        self.test_paths = self.get_test_paths()
        self.test_tables = self.setup_tables()

        self.list_framework_tests()

    def get_test_paths(self):
        test_paths = CONF[self.app_args.framework].test_paths
        test_paths = test_paths.split(",")
        result = []

        for path in test_paths:
            result = [x[0] for x in os.walk(
                os.path.join(CONF.DEFAULT.files_dir, "frameworks",
                             self.app_args.framework, path))]

        return sorted(result)

    def setup_tables(self):
        test_tables = []

        longest_path = (max(self.test_paths, key=len))
        longest_path_length = len(longest_path)

        for path in self.test_paths:
            if longest_path_length % 2 == 0:
                if len(path) % 2 != 0:
                    path += " "

            elif longest_path_length % 2 != 0:
                if len(path) % 2 == 0:
                    path += " "

            table = PrettyTable([path])
            if path != longest_path:
                table.padding_width = ((longest_path_length - len(
                    path)) / 2) + 1
            test_tables.append(table)

        return test_tables

    def list_framework_tests(self):
        for i, path in enumerate(self.test_paths):
            if os.path.isdir(path):
                for filename in sorted(os.listdir(path)):
                    if self.tests_format in filename:
                        self.test_tables[i].add_row([filename])
            else:
                LOG.error("tests path %s does not exist. framework provided"
                          " may not be a supported framework.", path)
        for table in self.test_tables:
            if len(table._rows) > 0:
                print(table)
