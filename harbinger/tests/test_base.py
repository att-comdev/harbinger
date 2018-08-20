import argparse
import os
import unittest

from harbinger.base import Base

import mock


class TestBase(unittest.TestCase):
    """Unit tests for Base"""

    description_value = None

    def setUp(self):
        self.args = mock.Mock(spec=argparse.Namespace)

        self.yaml_file = os.path.join(os.path.dirname(__file__),
                                      "data/test_yaml.yaml")
        self.test_object = Base(app=mock.Mock(), app_args=self.args)

    def test_get_parser(self):
        parser = self.test_object.get_parser('NAME')
        self.assertEqual('NAME', parser.prog)

    def test_load_yaml(self):
        file = self.test_object.load_yaml(self.yaml_file)
        self.assertIn("Execute", file)
