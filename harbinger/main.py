# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import sys

import logging as consoleLogging
import multiprocessing_logging

from cliff.app import App
from cliff.commandmanager import CommandManager
from oslo_config import cfg
from oslo_log import log as logging

from harbinger import __version__
from harbinger.common.color_logs import ColorLogFormatter

LOG = logging.getLogger(__name__)
CONF = cfg.CONF
DOMAIN = "harbinger"


class Harbinger(App):
    def __init__(self):
        super(Harbinger, self).__init__(
            command_manager=CommandManager('harbinger.commands'),
            deferred_help=True,
            description='Manager for Data Plane Testing Frameworks',
            version=__version__)

    def configure_logging(self):
        root_logger = consoleLogging.getLogger('')
        console = consoleLogging.StreamHandler(self.stdout)
        console_level = {
            0: consoleLogging.WARNING,
            1: consoleLogging.INFO,
            2: consoleLogging.DEBUG,
        }.get(self.options.verbose_level, consoleLogging.INFO)
        console.setLevel(console_level)
        console.setFormatter(ColorLogFormatter())
        root_logger.addHandler(console)

        multiprocessing_logging.install_mp_handler()

    # pylint: disable=W0613
    def initialize_app(self, argv):
        LOG.info('Initializing Harbinger')

    def prepare_to_run_command(self, cmd):
        LOG.debug("Preparing to execute " +
                  "command :: %s" % cmd.__class__.__name__)

    # pylint: disable=W0613
    def clean_up(self, cmd, result, err):
        LOG.debug("Cleaning Up %s" % cmd.__class__.__name__)
        if err:
            LOG.error("Encountered Error: %s" % err)


def harbingeropts(harbinger_config_file):
    if not os.path.exists(harbinger_config_file):
        raise IOError('%s file not present ' % harbinger_config_file)
    args = ['--config-file', harbinger_config_file]
    logging.register_options(CONF)
    CONF(args=args)
    logging.setup(CONF, DOMAIN)


# pylint: disable=W0102
def main(argv=sys.argv[1:]):
    harbingeropts(
        os.path.dirname(os.path.realpath(__file__)) + '/etc/harbinger.cfg')
    harbingerapp = Harbinger()
    return harbingerapp.run(argv)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
