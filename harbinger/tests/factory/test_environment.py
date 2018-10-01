import argparse
import os
import unittest

import mock

from harbinger.base import Base
from harbinger.factory.environment import Environment


class TestEnvironment(unittest.TestCase):
    """Unit tests for Environment"""

    def setUp(self):
        self.args = mock.Mock(spec=argparse.Namespace)
        self.yaml = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 "data/test_yaml.yaml")

        self.base_object = Base(app=mock.Mock(), app_args=self.args)
        self.yaml_file = self.base_object.load_yaml(self.yaml)

    def test__init(self):
        self.test_object = Environment(self.yaml_file["Environment"])
        self.assertEqual("v2", self.test_object.OS_API_VERSION)
