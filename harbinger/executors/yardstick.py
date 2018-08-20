"""
YardsstickExecutor class:
    - yardstick framework execution class
"""
import collections
import ConfigParser
import os
import oyaml as yaml

from oslo_config import cfg
from oslo_log import log as logging

from harbinger.common.utils import Utils
from harbinger.executors.base import BaseExecutor

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class YardstickExecutor(BaseExecutor):
    def __init__(self, framework, environment, options):
        super(YardstickExecutor, self).__init__(framework, environment,
                                                options)
        self.conf_file_name = self.framework.name + ".conf"
        self.inputs_path = os.path.join(CONF.DEFAULT.files_dir, "inputs")
        self.outputs_path = os.path.join(CONF.DEFAULT.files_dir, "outputs")
        self.outputs_full_path = os.path.join(self.outputs_path,
                                              "yardstick.out")
        self.conf_full_path = os.path.join(self.inputs_path,
                                           self.conf_file_name)
        self.test_paths = os.path.join(CONF[self.framework.name].test_paths)
        self.test_suite_name = "yardstick-suite.yaml"

        self.config = ConfigParser.RawConfigParser()

    def setup(self):
        super(YardstickExecutor, self).setup()

        # check flavor
        flavor_name = Utils.hierarchy_lookup(self, 'flavor_name')
        flavor_exists = self.flavor.check_flavor(flavor_name)
        if flavor_exists is False:
            self.flavor.create_flavor(name=flavor_name, ram='512',
                                      vcpus='1', disk='3', swap='100')

        # check image
        image_name = Utils.hierarchy_lookup(self, 'image')
        image_exists = self.image.check_image(image_name)

        if image_exists is False:
            self.create_image()
            self.image.upload_image(image_name, 'qcow2', 'bare',
                                    '/tmp/workspace/yardstick/')

        self.create_yardstick_conf()

        test_list = self.collect_tests()
        self.create_test_suite(test_list)

        # set additional environment variables necessary for openstack api
        Utils.source_openrc(self)

        run_command = "yardstick --config-file " + str(self.conf_full_path)
        run_command += " task start"
        run_command += " --output-file " + str(self.outputs_full_path)
        run_command += " --suite " + \
                       str(os.path.join(self.inputs_path,
                                        self.test_suite_name))

        self._exec_cmd(run_command)

    def collect_tests(self):
        tests_list = self.framework.tests
        suite = []
        for test in tests_list:
            test_dict = {'file_name': test}
            suite.append(test_dict)

        return suite

    def create_test_suite(self, test_list):
        test_suite_yaml = collections.OrderedDict()
        test_suite_yaml["schema"] = Utils.hierarchy_lookup(self, 'schema')
        test_suite_yaml["name"] = self.test_suite_name

        # Check if test_cases_dir is necessary

        if not any(self.test_paths[:-1] in test["file_name"]
                   for test in test_list):
            test_suite_yaml["test_cases_dir"] = self.test_paths
        else:
            test_suite_yaml["test_cases_dir"] = '/'

        test_suite_yaml["test_cases"] = test_list

        file_contents = yaml.dump(test_suite_yaml, default_flow_style=False)

        with open(os.path.join(self.inputs_path,
                               self.test_suite_name), 'w') as yaml_file:
            yaml_file.write(file_contents)

    def add_extras_options(self):
        for key, value in self.framework.extras.iteritems():
            self.config.set("DEFAULT", str(key), value)

    def create_yardstick_conf(self):
        with open(self.conf_full_path, "wb") as configfile:
            if hasattr(self.framework, 'extras'):
                self.add_extras_options()

            debug = Utils.hierarchy_lookup(self, "debug")
            dispatcher = Utils.hierarchy_lookup(self, "dispatcher")
            dispatch_file = Utils.hierarchy_lookup(self,
                                                   "dispatcher_file_name")
            dispatch_file = os.path.join(self.outputs_path, dispatch_file)

            self.config.set("DEFAULT", "debug", debug)
            self.config.set("DEFAULT", "dispatcher", dispatcher)

            self.config.add_section("dispatcher_file")
            self.config.set("dispatcher_file", "file_name", dispatch_file)

            self.config.set("DEFAULT", "debug",
                            Utils.hierarchy_lookup(self, "debug"))

            self.config.write(configfile)

    def create_image(self):
        # this has to run as root, in the container root is the default user
        LOG.info('Creating Yardstick image..')

        os.environ['YARD_IMG_ARCH'] = 'amd64'
        Utils.source_openrc(self)

        yrdstick_path = os.path.join(CONF.DEFAULT.files_dir,
                                     "frameworks/yardstick/")
        image_modify = yrdstick_path + 'tools/yardstick-img-modify'
        cloud_modify = yrdstick_path + 'tools/ubuntu-server-cloudimg-modify.sh'

        script_path = image_modify + " " + cloud_modify

        self._exec_cmd('apt update && ' + script_path)
