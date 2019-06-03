"""
ShakerExecutor class:
    - shaker framework execution class
"""
import configparser
import os

from oslo_config import cfg
from oslo_log import log as logging

from harbinger.common.utils import Utils
from harbinger.executors.base import BaseExecutor

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class ShakerExecutor(BaseExecutor):
    def __init__(self, framework, environment, options):
        super(ShakerExecutor, self).__init__(framework, environment, options)
        self.cfg_file_name = self.framework.name + ".cfg"
        self.cfg_full_path = os.path.join(self.inputs_dir, self.cfg_file_name)
        self.results_json_path = os.path.join(self.outputs_dir,
                                              "shaker-results.json")
        self.collected_tests_list = self.collect_tests()
        self.formated_tests = self.format_collected_tests(
            self.collected_tests_list)
        self.config = configparser.RawConfigParser()

    def setup(self):
        super(ShakerExecutor, self).setup()

        image_name = Utils.hierarchy_lookup(self, 'image')
        image_exists = self.image.check_image(image_name)

        if image_exists is False:
            self.create_image()
            self.image.upload_image(image_name, 'qcow2', 'bare')

        self.create_cfg_file()
        self._exec_cmd("shaker --config-file " + self.cfg_full_path)

    def add_extras_options(self):
        for key, value in self.framework.extras.items():
            self.config.set("DEFAULT", str(key), value)

    def format_collected_tests(self, collected_tests_list):
        collected_tests_string = ""
        for test in collected_tests_list:
            collected_tests_string += test + ", "

        return collected_tests_string

    def create_cfg_file(self):
        if hasattr(self.framework, 'extras'):
            self.add_extras_options()

        username = Utils.hierarchy_lookup(self, 'username')
        password = Utils.hierarchy_lookup(self, 'password')
        project_name = Utils.hierarchy_lookup(self, 'project_name')
        user_domain_name = Utils.hierarchy_lookup(self, 'user_domain_name')
        user_domain_id = Utils.hierarchy_lookup(self, 'user_domain_id')
        project_domain_name = Utils.hierarchy_lookup(self,
                                                     'project_domain_name')
        project_domain_id = Utils.hierarchy_lookup(self, 'project_domain_id')
        flavor_name = Utils.hierarchy_lookup(self, 'flavor_name')
        image_name = Utils.hierarchy_lookup(self, 'image')
        output = self.results_json_path
        scenario = self.formated_tests
        server_endpoint = Utils.hierarchy_lookup(self, 'server_endpoint')
        external_net = Utils.hierarchy_lookup(self, 'external_network')

        user_domain = user_domain_name or user_domain_id
        project_domain = project_domain_name or project_domain_id

        self.config.set("DEFAULT", "os_username", username)
        self.config.set("DEFAULT", "os_password", password)
        self.config.set("DEFAULT", "os_project_name", project_name)
        self.config.set("DEFAULT", "os_user_domain_name", user_domain)
        self.config.set("DEFAULT", "os_project_domain_name", project_domain)
        self.config.set("DEFAULT", "flavor_name", flavor_name)
        self.config.set("DEFAULT", "image_name", image_name)
        self.config.set("DEFAULT", "output", output)
        self.config.set("DEFAULT", "scenario", scenario)
        self.config.set("DEFAULT", "server_endpoint", server_endpoint)
        self.config.set("DEFAULT", "external_net", external_net)

        with open(self.cfg_full_path, 'w') as configfile:
            self.config.write(configfile)

    def create_image(self):
        Utils.source_openrc(self)
        self._exec_cmd("shaker-image-builder")
