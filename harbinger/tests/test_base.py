import argparse
import copy
import os
import unittest

import mock

from harbinger import base


class TestBase(unittest.TestCase):
    """Unit tests for Base"""
    def setUp(self):
        self.args = mock.Mock(spec=argparse.Namespace)
        self.yaml_file = os.path.join(os.path.dirname(__file__),
                                      "data/test_yaml.yaml")
        self.test_object = base.Base(app=mock.Mock(), app_args=self.args)

    def test_load_yaml(self):
        file = self.test_object.load_yaml(self.yaml_file)
        self.assertIn("Execute", file)

    def test_harbingeropts_error(self):
        self.assertRaises(IOError, base.harbingeropts, '')

    def test_harbingeropts_success(self):
        self.assertGreater(len(base.OPTS), 0)
        original_opts = copy.deepcopy(base.OPTS)
        base.OPTS = []
        self.assertEqual(len(base.OPTS), 0)

        base.harbingeropts(
            os.path.dirname(os.path.realpath(__file__)) +
            '/../etc/harbinger.cfg')

        self.assertEqual(len(base.OPTS), len(original_opts))

    def test_existing_register_opt_group(self):
        base.OPTS = []
        test_conf = base.harbingeropts(
            os.path.dirname(os.path.realpath(__file__)) +
            '/../etc/harbinger.cfg')

        for group, option in base.OPTS:
            base.register_opt_group(test_conf, group, option)

        base.register_opt_group(test_conf, [], [])
        self.assertEqual(base.CONF, test_conf)

    def test_take_action(self):
        self.test_object.take_action(self.args)


class TestCommandBase(unittest.TestCase):
    def setUp(self):
        self.args = mock.Mock(spec=argparse.Namespace)
        self.test_object = base.CommandBase(app=mock.Mock(),
                                            app_args=self.args)

    def test_get_parser(self):
        parser = self.test_object.get_parser('NAME')
        self.assertEqual('NAME', parser.prog)
