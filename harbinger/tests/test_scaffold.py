import argparse
import os
import unittest

import mock
from testfixtures import log_capture

from harbinger.scaffold import Scaffold


class TestScaffold(unittest.TestCase):

    def setUp(self):
        args = mock.Mock(spec=argparse.Namespace)
        args.framework = 'test_framework'
        self.test_object = Scaffold(app=mock.Mock(), app_args=args)

    def test_get_description(self):
        expected = "creates boiler plate framework file and " \
                   "harbinger.cfg option for framework"
        self.assertEqual(expected, self.test_object.get_description())

    def test_get_parser(self):
        parser = self.test_object.get_parser('NAME')
        self.assertEqual('NAME', parser.prog)
        parsed = parser.parse_args(['test_framework'])
        self.assertEqual(parsed.framework, 'test_framework')

    @mock.patch.object(Scaffold, 'create_executor_file')
    @mock.patch.object(Scaffold, 'create_venv_directories')
    @mock.patch.object(Scaffold, 'create_framework_directories')
    @mock.patch.object(Scaffold, 'add_framework_section')
    @mock.patch('ConfigParser.RawConfigParser')
    @mock.patch('os.path.dirname', return_value='test_path')
    def test_take_action(self, mock_dirname, mock_cfg_parser,
                         mock_add_framework_section,
                         mock_create_framework_dirs,
                         mock_create_venv_dirs,
                         mock_create_executor_file):
        parsed_args = mock.Mock(spec=argparse.Namespace)
        parsed_args.framework = 'test_framework'
        self.test_object.take_action(parsed_args)
        mock_dirname.assert_called()
        mock_cfg_parser.assert_has_calls([
            mock.call().read('test_path/etc/harbinger.cfg'),
        ])
        mock_add_framework_section.assert_called()
        mock_create_framework_dirs.assert_called()
        mock_create_venv_dirs.assert_called()
        mock_create_executor_file.assert_called_once_with(
            'Test_frameworkExecutor')

    def test_add_framework_section(self):
        self.test_object.config = mock.MagicMock()
        self.test_object.harbinger_cfg_path = 'test_path'
        mock_open = mock.mock_open()
        open_name = 'harbinger.scaffold.open'
        with mock.patch(open_name, mock_open, create=True):
            self.test_object.add_framework_section()
        self.test_object.config.add_section.assert_called_once_with(
            'test_framework')
        self.test_object.config.write.assert_called_once()

    @log_capture()
    def test_add_framework_section_exception(self, capture):
        self.test_object.config = mock.MagicMock()
        mock_add_section = mock.MagicMock()
        mock_add_section.side_effect = Exception()
        self.test_object.config.add_section = mock_add_section
        self.test_object.add_framework_section()
        capture.check(
            ('harbinger.scaffold', 'INFO',
             'Adding harbinger.cfg test_framework section'),
            ('harbinger.scaffold', 'WARNING',
             'Section test_framework already exists'),
        )

    @mock.patch('harbinger.scaffold.CONF')
    @mock.patch('os.makedirs')
    def test_create_framework_dirs(self, mock_makedirs, mock_conf):
        mock_conf.DEFAULT.files_dir = 'test_dir'
        self.test_object.create_framework_directories()
        mock_makedirs.assert_called_once_with(
            'test_dir/frameworks/test_framework/test_framework')

    @log_capture()
    @mock.patch('harbinger.scaffold.CONF')
    @mock.patch('os.makedirs')
    def test_create_framework_dirs_exception(self, mock_makedirs,
                                             mock_conf, capture):
        mock_conf.DEFAULT.files_dir = 'test_dir'
        mock_makedirs.side_effect = Exception()
        self.test_object.create_framework_directories()
        capture.check(
            ('harbinger.scaffold', 'INFO',
             'Creating framework directory test_framework'),
            ('harbinger.scaffold', 'WARNING',
             'Directory test_dir/frameworks/test_framework'
             '/test_framework already exists'),
        )

    @mock.patch('harbinger.scaffold.CONF')
    @mock.patch('os.makedirs')
    def test_create_venv_dirs(self, mock_makedirs, mock_conf):
        mock_conf.DEFAULT.files_dir = 'test_dir'
        self.test_object.create_venv_directories()
        mock_makedirs.assert_called_once_with(
            'test_dir/venvs/test_framework')

    @log_capture()
    @mock.patch('harbinger.scaffold.CONF')
    @mock.patch('os.makedirs')
    def test_create_venvs_dirs_exception(self, mock_makedirs,
                                         mock_conf, capture):
        mock_conf.DEFAULT.files_dir = 'test_dir'
        mock_makedirs.side_effect = Exception()
        self.test_object.create_venv_directories()
        capture.check(
            ('harbinger.scaffold', 'INFO',
             'Creating venvs directory test_framework'),
            ('harbinger.scaffold', 'WARNING',
             'Directory test_dir/venvs/test_framework already exists'),
        )

    def test_create_executor_file(self):
        self.test_object.executor_path = 'foo'
        mock_open = mock.mock_open()
        open_name = 'harbinger.scaffold.open'
        with mock.patch(open_name, mock_open, create=True):
            self.test_object.create_executor_file('test_class')
        handle = mock_open()
        base_path = os.path.dirname(os.path.realpath(__file__))
        data_path = os.path.join(base_path, "data")
        expected_file_name = "%s/executor_output.generatedpy" % data_path
        with open(expected_file_name, 'r') as data_file:
            expected = data_file.read()
        handle.write.assert_called_once_with(expected)
