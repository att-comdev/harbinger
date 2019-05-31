import argparse
import unittest

import mock

from harbinger.base import Base  # noqa
from harbinger.common.directory_manager import \
    DirectoryManager


class TestDirectoryManager(unittest.TestCase):

    def setUp(self):
        self.args = mock.Mock(spec=argparse.Namespace)
        self.test_object = DirectoryManager()

    @mock.patch('harbinger.common.directory_manager.os', autospec=True)
    def test_setup(self, mock_os):
        mock_os.path.isdir.return_value = False

        self.test_object.setup()

        calls = [
            mock.call(self.test_object.inputs_dir),
            mock.call(self.test_object.outputs_dir)
        ]

        mock_os.path.isdir.assert_has_calls(calls)
        mock_os.makedirs.assert_has_calls(calls)

    @mock.patch('harbinger.common.directory_manager.os', autospec=True)
    def test_setup_bad_dirs(self, mock_os):
        mock_os.makedirs.side_effect = OSError

        self.test_object.setup()

        self.assertRaises(OSError)

    @mock.patch('harbinger.common.directory_manager.os', autospec=True)
    def test_archive_outputs(self, mock_os):
        self.test_object.setup()

        mock_os.walk.return_value = [
            ('.', ['dir1'], ['file1'])
        ]

        with mock.patch("builtins.open",
                        mock.mock_open(read_data="data")) as mock_file:
            self.test_object.archive_outputs()
            self.assertEqual(open("path/to/open").read(), "data")
            mock_file.assert_called_with("path/to/open")

    @mock.patch('harbinger.common.directory_manager.os', autospec=True)
    def test_archive_outputs_bad(self, mock_os):
        self.test_object.setup()

        mock_os.walk.return_value = []

        with mock.patch("builtins.open") as mock_file:
            self.test_object.archive_outputs()
            mock_file.assert_not_called()
