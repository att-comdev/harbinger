import argparse
import unittest

import mock
from prettytable import PrettyTable

from harbinger.list_frameworks import ListFrameworks


class TestListFrameworks(unittest.TestCase):

    def setUp(self):
        self.args = mock.Mock(spec=argparse.Namespace)
        self.test_object = ListFrameworks(
            app=mock.Mock(),
            app_args=self.args
        )

    def test_get_description(self):
        _description = "lists all supported frameworks"
        self.assertEqual(
            _description,
            self.test_object.get_description()
        )

    def test_get_parser(self):
        _parser = self.test_object.get_parser('test_prog')
        self.assertEqual(_parser.prog, 'test_prog')

    @mock.patch.object(ListFrameworks, 'log_frameworks')
    @mock.patch('harbinger.list_frameworks.Utils', autospec=True)
    def test_take_action(self, mock_utils, mock_list_frameworks):
        parsed_args = mock.Mock(spec=argparse.Namespace)
        _supported_frameworks = ['frame1', 'frame2', 'frame3']
        mock_utils.get_supported_frameworks.return_value = (
            _supported_frameworks
        )

        self.test_object.take_action(parsed_args)

        mock_list_frameworks.assert_called_once_with(
            _supported_frameworks
        )

    @mock.patch('sys.stdout', autospec=True)
    def test_log_frameworks(self, mock_print):
        _supported_frameworks = ['frame1', 'frame2', 'frame3']
        calls = [
            mock.call.write(
                "+------------+\n"
                "| Frameworks |\n"
                "+------------+\n"
                "|   frame1   |\n"
                "|   frame2   |\n"
                "|   frame3   |\n"
                "+------------+"
            )
        ]
        self.test_object.framework_tables = PrettyTable(["Frameworks"])
        self.test_object.log_frameworks(_supported_frameworks)

        mock_print.assert_has_calls(calls)
