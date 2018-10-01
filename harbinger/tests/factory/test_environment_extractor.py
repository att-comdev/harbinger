import argparse
import os
import unittest

import mock

from harbinger.base import Base
from harbinger.factory.environment_extractor import \
    EnvironmentExtractor


class TestEnvironmentExtractor(unittest.TestCase):
    """Unit tests for EnvironmentExtractor"""

    description_value = None

    def setUp(self):
        self.args = mock.Mock(spec=argparse.Namespace)

        self.yaml = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 "data/test_yaml.yaml")

        self.base_object = Base(app=mock.Mock(), app_args=self.args)
        self.yaml_file = self.base_object.load_yaml(self.yaml)

        self.test_object = EnvironmentExtractor()

    def test_parse_framework(self):
        self.environment = self.test_object.parse_environment(self.yaml_file)
        self.assertEqual("v2", self.environment.OS_API_VERSION)
