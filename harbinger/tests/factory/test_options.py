import argparse
import os
import unittest

import mock

from harbinger.base import Base
from harbinger.factory.options import Options


class TestOptions(unittest.TestCase):
    """Unit tests for Options"""

    def setUp(self):
        self.args = mock.Mock(spec=argparse.Namespace)
        self.yaml = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                 "data/test_yaml.yaml")

        self.base_object = Base(app=mock.Mock(), app_args=self.args)
        self.yaml_file = self.base_object.load_yaml(self.yaml)

    def test__init(self):
        self.test_object = Options(self.yaml_file["Options"])
        self.assertEqual("myTestProject", self.test_object.project_name)
