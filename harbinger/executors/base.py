"""
BaseExecutor class:
    - a Base class for executing a framework. All other frameworks
    will inheret from this class
"""

import os
import shlex
import subprocess

from oslo_config import cfg
from oslo_log import log as logging

from harbinger.common.utils import Utils
from harbinger.flavors.flavor_manager import FlavorManager
from harbinger.images.image_manager import ImageManager

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class BaseExecutor():
    def __init__(self, framework, environment, options):
        self.inputs_dir = os.path.join(CONF.DEFAULT.files_dir, "inputs")
        self.outputs_dir = os.path.join(CONF.DEFAULT.files_dir, "outputs")
        self.framework = framework
        self.environment = environment
        self.options = options
        self.relative_path = os.path.join(
            CONF.DEFAULT.files_dir, "frameworks",
            self.framework.name, Utils.hierarchy_lookup(self, "test_paths"))

        os.environ["OS_PROJECT_DOMAIN_NAME"] = "default"
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
        for attr, value in self.environment.__dict__.items():
            if attr.isupper():
                os.environ[attr] = value

        # set environment_overrides present in input.yaml
        attr = getattr(self.framework, 'environment_overrides', None)
        if attr is not None:
            for key, value in attr.items():
                if key.isupper():
                    os.environ[key] = value

    def create_image(self):
        """create image needed by framework

        this method is a stub, create_image should be implemented in the
        correct framework executor class and should use that framework's
        native approach for creating images

        """
        raise NotImplementedError()

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

        if return_code != 0:
            raise RuntimeError('command <%s> failed with return code %s' % (
                command, return_code))

        return output

    def walk_directory(self, directory):
        test_list = []
        for dir_name, subdir_list, file_list in os.walk(directory,
                                                        topdown=False):
            for file_name in file_list:
                if file_name.endswith(CONF.shaker.tests_format):
                    test_list.append(os.path.join(dir_name, file_name))
        return test_list

    def valid_schema_value(self, value):
        valid = False
        if value[-1] == "/":
            valid = True
        else:
            end_of_path = os.path.basename(os.path.normpath(value))
            if "." in end_of_path:
                valid = True

        return valid

    def collect_tests(self):
        framework_tests = self.framework.tests
        test_list = []
        bad_test_list = []
        invalid_schema_value = []

        for test in framework_tests:
            if test == "*":
                test_list += self.walk_directory(self.relative_path)
            elif not self.valid_schema_value(test):
                invalid_schema_value.append(test)
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

        if len(invalid_schema_value) > 0:
            raise RuntimeError(
                'There are one or more values under tests that'
                ' violate the schema.\nAll paths must end in'
                ' a file extention or / to indicate a file or directory:\n'
                '%s' % invalid_schema_value)

        if len(bad_test_list) > 0:
            raise RuntimeError(
                'There are one or more tests, test paths,'
                ' or directories that do not exist or have'
                ' invalid extensions:\n%s' % bad_test_list)

        return test_list
