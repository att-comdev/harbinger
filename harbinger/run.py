"""
Run class:
    - extracts all the appropriate frameworks and environment
    data from the yaml file and proceeds to run the relevant
    frameworks
"""
import multiprocessing
import os
import signal
import StringIO
import traceback

from oslo_config import cfg
from oslo_log import log as logging
from psutil import Process
from pykwalify.core import Core

from harbinger import base
from harbinger.common.directory_manager import \
    DirectoryManager
from harbinger.common.utils import Utils
from harbinger.factory.environment_extractor \
    import EnvironmentExtractor
from harbinger.factory.framework_extractor import \
    FrameworkExtractor
from harbinger.factory.options_extractor import \
    OptionsExtractor

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class Run(base.CommandBase):
    description = "run harbinger by providing a yaml file"

    def get_description(self):
        return self.description

    def get_parser(self, prog_name):
        parser = super(Run, self).get_parser(prog_name)

        return parser

    def parse_frameworks(self):
        self.frameworks_dict = self.framework_extractor.parse_frameworks(
            self.app_args.yaml_file)

    def parse_environment(self):
        self.environment = self.environment_extractor.parse_environment(
            self.app_args.yaml_file)

    def parse_options(self):
        self.options = self.options_extractor.parse_options(
            self.app_args.yaml_file)

    def take_action(self, parsed_args):
        self.directory_manager = DirectoryManager()
        self.directory_manager.setup()

        self.app_args.yaml_file = self.load_yaml(parsed_args.yaml)
        self.framework_extractor = FrameworkExtractor()
        self.environment_extractor = EnvironmentExtractor()
        self.options_extractor = OptionsExtractor()

        self.parse_frameworks()
        self.parse_environment()
        self.parse_options()

        self.begin()

    def begin(self):
        schema_file = self.load_yaml(
            os.path.dirname(__file__) + "/schemas/input.yaml")

        core = Core(source_data=self.app_args.yaml_file,
                    schema_data=schema_file)
        core.validate(raise_exception=True)

        self.directory_manager.archive_outputs()

        if self.options.execution_mode == 'serial':
            self.execute_serial()
        else:
            # paralell is default
            self.execute_parallel()

        LOG.info('All frameworks have finished execution')

    def execute_serial(self):
        LOG.info('Executing frameworks %s in serial',
                 self.frameworks_dict.keys())

        for item in self.frameworks_dict:
            worker([item, self.frameworks_dict[item], self.environment,
                    self.options])

    def execute_parallel(self):
        LOG.info('Executing frameworks %s in parallel',
                 self.frameworks_dict.keys())

        results = []
        parent_id = os.getpid()
        pool = multiprocessing.Pool(initializer=worker_init(parent_id))
        for item in self.frameworks_dict:
            results.append(pool.apply_async(worker, [(item,
                                                      self.frameworks_dict[
                                                          item],
                                                      self.environment,
                                                      self.options)]))

        pool.close()
        pool.join()

        for outcome in results:
            # call get so any thrown exceptions are correctly raised
            outcome.get()


def loader(name, framework, environment, options):
    # alter the name to correctly find the class e.g. go from shaker to Shaker
    class_name = name.title()
    cls = Utils.load_class(
        'harbinger.executors.' + name
        + '.' + class_name + 'Executor')
    framework_executor = cls(framework, environment, options)
    framework_executor.setup()


def worker_init(parent_id):
    def sig_int(signal_num, frame):
        LOG.error('signal: %s frame: %s', signal_num, frame)
        parent = Process(parent_id)
        for child in parent.children():
            if child.pid != os.getpid():
                LOG.error("exiting child: %s" % child.pid)
                child.kill()
        LOG.error("exiting parent: %s" % parent_id)
        parent.kill()
        LOG.error("exiting all: %s" % os.getpid())
        Process(os.getpid()).kill()
    signal.signal(signal.SIGINT, sig_int)


def worker(args):
    try:
        multiprocessing.current_process().name = args[0] + '-worker'
        return loader(*args)
    except Exception:
        # this is used to correctly capture traceback from exceptions
        exc_buffer = StringIO.StringIO()
        traceback.print_exc(file=exc_buffer)
        LOG.error(exc_buffer.getvalue())
        raise
