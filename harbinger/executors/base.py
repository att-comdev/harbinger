"""
BaseExecutor class:
    - a Base class for executing a framework. All other frameworks
    will inheret from this class
"""

import os
import shlex
import subprocess

from harbinger.common.utils import Utils
from harbinger.flavors.flavor_manager import FlavorManager
from harbinger.images.image_manager import ImageManager
from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class BaseExecutor(object):
    def __init__(self, framework, environment, options):
        self.inputs_dir = os.path.join(CONF.DEFAULT.files_dir, "inputs")
        self.outputs_dir = os.path.join(CONF.DEFAULT.files_dir, "outputs")
        self.framework = framework
        self.environment = environment
        self.options = options
        self.relative_path = os.path.join(
            CONF.DEFAULT.files_dir, "frameworks",
            self.framework.name, Utils.hierarchy_lookup(self, "test_paths"))

        self.image = ImageManager(self.framework.name,
                                  self.environment.OS_AUTH_URL +
                                  self.environment.OS_API_VERSION,
                                  self.options.username, self.options.password,
                                  self.options.project)

        self.flavor = FlavorManager(self.framework.name,
                                    self.environment.OS_AUTH_URL +
                                    self.environment.OS_API_VERSION,
                                    self.options.username,
                                    self.options.password,
                                    self.options.project)

    def setup(self):
        self.export_environment()

    def export_environment(self):
        """setup environment variables

        this method sets environment variables (all uppsercase) from the
        Envronment section of input yaml as python environment variables

        """
        for attr, value in self.environment.__dict__.iteritems():
            if attr.isupper():
                os.environ[attr] = value

        # set environment_overrides present in input.yaml
        attr = getattr(self.framework, 'environment_overrides', None)
        if attr is not None:
            for key, value in attr.iteritems():
                if key.isupper():
                    os.environ[key] = value

    def create_image(self):
        """create image needed by framework

        this method is a stub, create_image should be implemented in the
        correct framework executor class and should use that framework's
        native approach for creating images

        """
        pass

    def _exec_cmd(self, command):
        LOG.info('Executing {%s}:\n', command)

        command_template = '/bin/bash -c ' \
                           '"source {}venvs/{}/bin/activate' \
                           ' && {}"'

        execute = shlex.split(command_template.format(CONF.DEFAULT.files_dir,
                                                      self.framework.name,
                                                      command))

        popen = subprocess.Popen(
            execute,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True)

        for stdout_line in iter(popen.stdout.readline, ""):
            LOG.info(stdout_line.rstrip(), extra={'plainOutput': True})

        output = popen.communicate()
        return_code = popen.returncode

        if return_code == 0:
            return output
        else:
            raise RuntimeError('command <%s> failed with return code %s' % (
                command, return_code))

    def walk_directory(self, directory):
        test_list = []
        for dir_name, subdir_list, file_list in os.walk(directory,
                                                        topdown=False):
            for file_name in file_list:
                if file_name.endswith(CONF.shaker.tests_format):
                    test_list.append(os.path.join(dir_name, file_name))
        return test_list

    def collect_tests(self):
        framework_tests = self.framework.tests
        test_list = []
        bad_test_list = []

        for test in framework_tests:
            if test == "*":
                test_list += self.walk_directory(self.relative_path)
            elif os.path.isabs(test) and os.path.exists(test):
                if os.path.isdir(test):
                    test_list += self.walk_directory(test)
                elif test.endswith(CONF.shaker.tests_format):
                    test_list.append(test)
                else:
                    bad_test_list.append(test)

            elif not os.path.isabs(test):
                relative_test = self.relative_path + test
                if os.path.exists(relative_test):
                    if os.path.isdir(relative_test):
                        test_list += self.walk_directory(relative_test)
                    elif test.endswith(CONF.shaker.tests_format):
                        test_list.append(relative_test)
                    else:
                        bad_test_list.append(test)
                else:
                    bad_test_list.append(test)

            else:
                bad_test_list.append(test)

        if len(bad_test_list) > 0:
            raise RuntimeError(
                'There are one or more tests, test paths, '
                'or directories that do not exist or have'
                ' invalid extensions. %s' % bad_test_list)

        return test_list
