import argparse
import os
import unittest

import mock

from harbinger.base import Base
from harbinger.factory.options_extractor import \
    OptionsExtractor


class TestOptionsExtractor(unittest.TestCase):
    """Unit tests for OptionsExtractor"""

    description_value = None

    def setUp(self):
        self.args = mock.Mock(spec=argparse.Namespace)

        self.yaml = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 "data/test_yaml.yaml")

        self.base_object = Base(app=mock.Mock(), app_args=self.args)
        self.yaml_file = self.base_object.load_yaml(self.yaml)

        self.test_object = OptionsExtractor()

    def test_parse_framework(self):
        self.options = self.test_object.parse_options(self.yaml_file)
        self.assertEqual("myTestProject", self.options.project_name)
