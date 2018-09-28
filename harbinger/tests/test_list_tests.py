import argparse
import sys
import unittest

import mock
from prettytable import PrettyTable
from testfixtures import log_capture

from harbinger.list_tests import ListTests


class TestListTests(unittest.TestCase):

    def setUp(self):
        args = mock.Mock(spec=argparse.Namespace)
        args.framework = 'test_framework'
        self.test_object = ListTests(app=mock.Mock(), app_args=args)

    def test_get_description(self):
        expected = "lists the tests for the framework provided"
        self.assertEqual(expected, self.test_object.get_description())

    def test_get_parser(self):
        parser = self.test_object.get_parser('NAME')
        self.assertEqual('NAME', parser.prog)
        parsed = parser.parse_args(['test_framework'])
        self.assertEqual(parsed.framework, 'test_framework')

    @log_capture()
    @mock.patch('harbinger.list_tests.CONF')
    @mock.patch.object(ListTests, 'get_test_paths')
    @mock.patch.object(ListTests, 'setup_tables')
    @mock.patch.object(ListTests, 'list_framework_tests')
    def test_take_action(self, mock_list_framework_tests, mock_setup_tables,
                         mock_get_test_paths, mock_conf, capture):
        parsed_args = mock.Mock(spec=argparse.Namespace)
        parsed_args.framework = 'test_framework'
        mock_conf['test_framework'].tests_format = 'tests_format'
        self.test_object.take_action(parsed_args)
        self.assertEqual(self.test_object.tests_format, 'tests_format')
        mock_get_test_paths.assert_called_once()
        mock_setup_tables.assert_called_once()
        mock_list_framework_tests.assert_called_once()
        capture.check(
            ('harbinger.list_tests', 'INFO', 'test_framework tests:\n'),
        )

    @mock.patch('harbinger.list_tests.CONF')
    def test_get_test_paths(self, mock_conf):
        mock_conf['test_framework'].test_paths = 'test_path1,test_path2'
        mock_conf.DEFAULT.files_dir = 'test_dir'

        def walker(test_path):
            # paths are intentionally unsorted
            paths = {
                'test_dir/frameworks/test_framework/test_path1': [
                    ('path1b', '', ''),
                    ('path1a', '', ''),
                ],
                'test_dir/frameworks/test_framework/test_path2': [
                    ('path2b', '', ''),
                    ('path2a', '', ''),
                ],
            }
            for path in paths[test_path]:
                yield path

        with mock.patch('os.walk') as mock_walk:
            mock_walk.side_effect = walker
            actual = self.test_object.get_test_paths()
            expected = ['path1a', 'path1b', 'path2a', 'path2b']
            self.assertEqual(actual, expected)

    def test_setup_tables(self):
        long_even_expected = ("+--------------------+\n"
                              "| long_path_even_len |\n"
                              "+--------------------+\n"
                              "+--------------------+")
        long_odd_expected = ("+-------------------+\n"
                             "| long_path_odd_len |\n"
                             "+-------------------+\n"
                             "+-------------------+")
        short_even_expected1 = ("+--------------------+\n"
                                "|     short_even     |\n"
                                "+--------------------+\n"
                                "+--------------------+")
        short_even_expected2 = ("+-------------------+\n"
                                "|    short_even     |\n"
                                "+-------------------+\n"
                                "+-------------------+")
        short_odd_expected1 = ("+--------------------+\n"
                               "|     short_odd      |\n"
                               "+--------------------+\n"
                               "+--------------------+")
        short_odd_expected2 = ("+-------------------+\n"
                               "|     short_odd     |\n"
                               "+-------------------+\n"
                               "+-------------------+")

        args = mock.Mock(spec=argparse.Namespace)
        test_object = ListTestsStub(app=mock.Mock(), app_args=args)
        test_paths = ['long_path_even_len', 'short_odd', 'short_even']
        expected = [long_even_expected,
                    short_odd_expected1,
                    short_even_expected1]
        test_object.set_test_paths(test_paths)
        actuals = test_object.setup_tables()
        for actual, expected in zip(actuals, expected):
            self.assertEqual(str(actual), expected)

        test_paths[0] = 'long_path_odd_len'
        expected = [long_odd_expected,
                    short_odd_expected2,
                    short_even_expected2]
        test_object.set_test_paths(test_paths)
        actuals = test_object.setup_tables()
        for actual, expected in zip(actuals, expected):
            self.assertEqual(str(actual), expected)

    @log_capture()
    @mock.patch('os.listdir')
    @mock.patch('os.path.isdir')
    def test_list_framework_tests(self, mock_isdir, mock_listdir, capture):
        args = mock.Mock(spec=argparse.Namespace)
        test_object = ListTestsStub(app=mock.Mock(), app_args=args)
        mock_isdir.side_effect = [True, False]
        mock_listdir.return_value = ['test_filename']
        test_paths = ['first_test_path', 'second_test_path']
        test_object.set_test_paths(test_paths)
        test_object.set_tests_format('filename')
        test_object.set_test_tables([PrettyTable([])])
        expected = ("+---------------+\n"
                    "|    Field 1    |\n"
                    "+---------------+\n"
                    "| test_filename |\n"
                    "+---------------+\n")

        # The following class and subsequent manipulations are
        # intended to check what is being put on stdout
        class StdoutMock(object):
            def __init__(self):
                self.data = []

            def write(self, data):
                self.data.append(data)

            def __str__(self):
                return "".join(self.data)

        orig_stdout = sys.stdout
        actual = StdoutMock()
        try:
            sys.stdout = actual
            test_object.list_framework_tests()
        finally:
            sys.stdout = orig_stdout
            actual = str(actual)

        self.assertEqual(actual, expected)
        capture.check(
            ('harbinger.list_tests', 'ERROR',
             "tests path second_test_path does not exist. framework "
             "provided may not be a supported framework."),
        )


class ListTestsStub(ListTests):
    def set_test_paths(self, test_paths):
        self.test_paths = test_paths

    def set_tests_format(self, tests_format):
        self.tests_format = tests_format

    def set_test_tables(self, test_tables):
        self.test_tables = test_tables
