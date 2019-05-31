import argparse
import unittest

import mock
from testfixtures import log_capture

from harbinger.remove_scaffold import RemoveScaffold


class TestRemoveScaffold(unittest.TestCase):

    def setUp(self):
        args = mock.Mock(spec=argparse.Namespace)
        args.framework = 'test_framework'
        self.test_object = RemoveScaffold(app=mock.Mock(), app_args=args)

    def test_get_description(self):
        expected = "removes and deletes all framework related files " \
                   "and references, including harbinger.cfg section"
        self.assertEqual(expected, self.test_object.get_description())

    def test_get_parser(self):
        parser = self.test_object.get_parser('NAME')
        self.assertEqual('NAME', parser.prog)
        parsed = parser.parse_args(['test_framework'])
        self.assertEqual(parsed.framework, 'test_framework')

    @log_capture()
    @mock.patch.object(RemoveScaffold, 'delete_executor_file')
    @mock.patch.object(RemoveScaffold, 'delete_venv_directories')
    @mock.patch.object(RemoveScaffold, 'delete_framework_directories')
    @mock.patch.object(RemoveScaffold, 'delete_framework_section')
    @mock.patch('configparser.RawConfigParser')
    @mock.patch('os.path.dirname', return_value='test_path')
    def test_take_action(self, mock_dirname, mock_cfg_parser,
                         mock_delete_framework_section,
                         mock_delete_venv_dirs,
                         mock_delete_framework_dirs,
                         mock_delete_executor_file, capture):
        parsed_args = mock.Mock(spec=argparse.Namespace)
        parsed_args.framework = 'test_framework'
        self.test_object.take_action(parsed_args)
        mock_dirname.assert_called()
        mock_cfg_parser.assert_has_calls([
            mock.call().read('test_path/etc/harbinger.cfg'),
        ])
        mock_delete_framework_section.assert_called_once()
        mock_delete_framework_dirs.assert_called_once()
        mock_delete_venv_dirs.assert_called_once()
        mock_delete_executor_file.assert_called_once()
        capture.check(
            ('harbinger.remove_scaffold', 'INFO', '---------------'),
            ('harbinger.remove_scaffold', 'INFO',
             'Make sure to remove references to framework in Dockerfile'),
            ('harbinger.remove_scaffold', 'INFO', '---------------'),
        )

    @log_capture()
    def test_delete_framework_section(self, capture):
        self.test_object.config = mock.MagicMock()
        self.test_object.harbinger_cfg_path = 'test_path'
        mock_open = mock.mock_open()
        open_name = 'harbinger.remove_scaffold.open'
        with mock.patch(open_name, mock_open, create=True):
            self.test_object.delete_framework_section()
        self.test_object.config.remove_section.assert_called_once_with(
            'test_framework')
        self.test_object.config.write.assert_called_once()
        capture.check(
            ('harbinger.remove_scaffold', 'INFO',
             'Deleting harbinger.cfg test_framework section'),
        )

    @log_capture()
    @mock.patch('os.remove')
    def test_delete_executor_file(self, mock_remove, capture):
        self.test_object.executor_path = 'test_path'
        self.test_object.delete_executor_file()
        mock_remove.assert_called_once_with('test_path')
        capture.check(
            ('harbinger.remove_scaffold', 'INFO',
             'Deleting test_framework framework executor file'),
        )

    @log_capture()
    @mock.patch('os.remove')
    def test_delete_executor_file_exception(self, mock_remove, capture):
        self.test_object.executor_path = 'test_path'
        mock_remove.side_effect = Exception()
        self.test_object.delete_executor_file()
        mock_remove.assert_called_once_with('test_path')
        capture.check(
            ('harbinger.remove_scaffold', 'INFO',
             'Deleting test_framework framework executor file'),
            ('harbinger.remove_scaffold', 'WARNING',
             'File test_path does not exist'),
        )

    @log_capture()
    @mock.patch('harbinger.remove_scaffold.CONF')
    @mock.patch('shutil.rmtree')
    def test_delete_framework_dirs(self, mock_rmtree, mock_conf, capture):
        mock_conf.DEFAULT.files_dir = 'test_dir'
        self.test_object.delete_framework_directories()
        mock_rmtree.assert_called_once_with(
            'test_dir/frameworks/test_framework')
        capture.check(
            ('harbinger.remove_scaffold', 'INFO',
             'Deleting framework directory test_framework'),
        )

    @log_capture()
    @mock.patch('harbinger.remove_scaffold.CONF')
    @mock.patch('shutil.rmtree')
    def test_delete_framework_dirs_exception(self, mock_rmtree,
                                             mock_conf, capture):
        mock_conf.DEFAULT.files_dir = 'test_dir'
        mock_rmtree.side_effect = Exception()
        self.test_object.delete_framework_directories()
        mock_rmtree.assert_called_once_with(
            'test_dir/frameworks/test_framework')
        capture.check(
            ('harbinger.remove_scaffold', 'INFO',
             'Deleting framework directory test_framework'),
            ('harbinger.remove_scaffold', 'WARNING',
             'Directory test_dir/frameworks/test_framework does not exist'),
        )

    @log_capture()
    @mock.patch('harbinger.remove_scaffold.CONF')
    @mock.patch('shutil.rmtree')
    def test_delete_venv_dirs(self, mock_rmtree, mock_conf, capture):
        mock_conf.DEFAULT.files_dir = 'test_dir'
        self.test_object.delete_venv_directories()
        mock_rmtree.assert_called_once_with('test_dir/venvs/test_framework')
        capture.check(
            ('harbinger.remove_scaffold', 'INFO',
             'Deleting venvs directory test_framework'),
        )

    @log_capture()
    @mock.patch('harbinger.remove_scaffold.CONF')
    @mock.patch('shutil.rmtree')
    def test_delete_venv_dirs_exception(self, mock_rmtree, mock_conf, capture):
        mock_conf.DEFAULT.files_dir = 'test_dir'
        mock_rmtree.side_effect = Exception()
        self.test_object.delete_venv_directories()
        mock_rmtree.assert_called_once_with('test_dir/venvs/test_framework')
        capture.check(
            ('harbinger.remove_scaffold', 'INFO',
             'Deleting venvs directory test_framework'),
            ('harbinger.remove_scaffold', 'WARNING',
             'Directory test_dir/venvs/test_framework does not exist'),
        )
