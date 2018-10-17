import os
import subprocess
import unittest

import mock
from testfixtures import log_capture

from harbinger.common.utils import Utils
from harbinger.executors.base import BaseExecutor


class TestBaseExecutor(unittest.TestCase):

    def setUp(self):
        self.mock_framework = mock.Mock()
        self.mock_framework.name = 'test_framework_name'

        self.mock_environment = mock.Mock()
        self.mock_environment.OS_AUTH_URL = 'test_os_auth_url'
        self.mock_environment.OS_API_VERSION = 'test_os_api_version'

        self.mock_options = mock.Mock()

    def _get_test_object(self):
        with mock.patch('harbinger.executors.base.CONF') as mock_conf:
            mock_conf.DEFAULT.files_dir = 'test_files_dir'
            with mock.patch.object(Utils, 'hierarchy_lookup') as mock_lookup:
                mock_lookup.return_value = 'test_paths'
                with mock.patch('harbinger.executors.base.FlavorManager'):
                    with mock.patch('harbinger.executors.base.ImageManager'):
                        test_object = BaseExecutor(
                            self.mock_framework,
                            self.mock_environment,
                            self.mock_options
                        )
            return test_object

    def test___init__(self):
        test_object = self._get_test_object()
        self.assertEqual(test_object.inputs_dir, 'test_files_dir/inputs')
        self.assertEqual(test_object.outputs_dir, 'test_files_dir/outputs')
        self.assertEqual(test_object.relative_path,
                         'test_files_dir/frameworks/'
                         'test_framework_name/test_paths')

    @mock.patch.object(BaseExecutor, 'export_environment')
    def test_setup(self, mock_export_environment):
        test_object = self._get_test_object()
        test_object.setup()
        mock_export_environment.assert_called()

    def test_export_environment(self):
        test_object = self._get_test_object()

        class Empty(object):
            pass

        test_object.environment = Empty()
        setattr(test_object.environment, 'ENVIRONMENT_KEY', 'ENVIRONMENT_VAL')
        setattr(test_object.environment, 'environment_key', 'environment_val')

        test_object.framework = Empty()

        with mock.patch.dict(os.environ, {}, clear=True):
            test_object.export_environment()
            self.assertIn('ENVIRONMENT_KEY', os.environ)
            self.assertEqual(os.environ['ENVIRONMENT_KEY'], 'ENVIRONMENT_VAL')
            self.assertNotIn('environment_key', os.environ)
            self.assertNotIn('FRAMEWORK_KEY', os.environ)
            self.assertNotIn('framework_key', os.environ)

        test_object.framework.environment_overrides = {
            'framework_key': 'framework_val',
            'FRAMEWORK_KEY': 'FRAMEWORK_VAL',
        }
        with mock.patch.dict(os.environ, {}, clear=True):
            test_object.export_environment()
            self.assertIn('ENVIRONMENT_KEY', os.environ)
            self.assertEqual(os.environ['ENVIRONMENT_KEY'], 'ENVIRONMENT_VAL')
            self.assertNotIn('environment_key', os.environ)
            self.assertIn('FRAMEWORK_KEY', os.environ)
            self.assertEqual(os.environ['FRAMEWORK_KEY'], 'FRAMEWORK_VAL')
            self.assertNotIn('framework_key', os.environ)

    def test_create_image(self):
        test_object = self._get_test_object()
        self.assertRaises(NotImplementedError, test_object.create_image)

    @log_capture()
    @mock.patch('subprocess.Popen')
    def test__exec_cmd(self, mock_popen_init, capture):

        class TestReadline(object):

            def __init__(self):
                self.called = False

            def __call__(self):
                if self.called:
                    return ''
                self.called = True
                return 'test_log_output'

        attrs = {
            'returncode': -1,
            'communicate.return_value': 'test_output',
            'stdout.readline': TestReadline()
        }
        mock_popen = mock.Mock(**attrs)
        mock_popen_init.return_value = mock_popen
        with mock.patch('harbinger.executors.base.CONF') as mock_conf:
            mock_conf.DEFAULT.files_dir = 'test_files_dir'
            test_object = self._get_test_object()
            with self.assertRaises(RuntimeError) as context:
                test_object._exec_cmd('test_command')
            exception = context.exception
            self.assertEqual(exception.message,
                             'command <test_command> '
                             'failed with return code -1')
            mock_popen_init.assert_called_once_with(
                [
                    '/bin/bash', '-c',
                    'source test_files_dirvenvs/test_framework_name/'
                    'bin/activate && test_command'
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
            capture.check(
                ('harbinger.executors.base', 'INFO',
                 'Executing {test_command}:\n'),
                ('harbinger.executors.base', 'INFO',
                 'test_log_output'),
            )

            mock_popen.returncode = 0
            output = test_object._exec_cmd('test_command')
            self.assertEqual(output, 'test_output')

    @mock.patch('harbinger.executors.base.CONF')
    def test_walk_directory(self, mock_conf):
        test_object = self._get_test_object()
        mock_conf.shaker.tests_format = 'fmt'

        with mock.patch('os.walk') as mock_walk:
            mock_walk.side_effect = walker
            actual = test_object.walk_directory('test_dir')
            self.assertListEqual(actual, ['test_dir/test_file.fmt'])

    def test_valid_schema_test(self):
        test_object = self._get_test_object()
        test = "test.fmt"
        self.assertTrue(test_object.valid_schema_value(test))
        test = "test/"
        self.assertTrue(test_object.valid_schema_value(test))
        test = "/test/"
        self.assertTrue(test_object.valid_schema_value(test))
        test = "test"
        self.assertFalse(test_object.valid_schema_value(test))

    @mock.patch('harbinger.executors.base.CONF')
    @mock.patch.object(BaseExecutor, 'walk_directory')
    @mock.patch.object(BaseExecutor, 'valid_schema_value')
    def test_collect_tests(self, mock_valid, mock_walk, mock_conf):
        test_object = self._get_test_object()
        mock_conf.shaker.tests_format = 'fmt'
        bad_path = 'There are one or more tests, test paths,' \
                   ' or directories that do not exist or have' \
                   ' invalid extensions:\n'
        invalid_path = 'There are one or more values under tests' \
                       ' that violate the schema.\nAll paths must' \
                       ' end in a file extention or / to indicate' \
                       ' a file or directory:\n'

        with mock.patch('os.path') as mock_path:

            test_object.framework.tests = ['*']
            mock_walk.return_value = ['test1/']
            self.assertListEqual((test_object.collect_tests()), ['test1/'])

            mock_path.isabs.return_value = True
            mock_path.exists.return_value = True
            mock_path.isdir.return_value = True
            test_object.framework.tests = ['test2/']
            mock_walk.return_value = ['test2/']
            self.assertListEqual((test_object.collect_tests()), ['test2/'])

            mock_path.isdir.return_value = False
            mock_valid.return_value = True
            test_object.framework.tests = ['test3.fmt']
            self.assertListEqual((test_object.collect_tests()), ['test3.fmt'])

            test_object.framework.tests = ['test4/']
            with self.assertRaises(RuntimeError) as context:
                test_object.collect_tests()
                self.assertEqual(context.exception.message,
                                 bad_path + '[\'test4\']')

            test_object.relative_path = 'test_path/'
            mock_path.isabs.return_value = False
            mock_path.isdir.return_value = True
            mock_path.exists.return_value = True
            test_object.framework.tests = ['test5/']
            mock_walk.return_value = ['test5/']
            self.assertListEqual(test_object.collect_tests(), ['test5/'])

            mock_path.isdir.return_value = False
            test_object.framework.tests = ['test6.fmt']
            self.assertListEqual(test_object.collect_tests(),
                                 ['test_path/test6.fmt'])

            test_object.framework.tests = ['test7/']
            with self.assertRaises(RuntimeError) as context:
                test_object.collect_tests()
                self.assertEqual(context.exception.message,
                                 bad_path + '[\'test7\']')

            mock_path.exists.return_value = False
            test_object.framework.tests = ['test8/']
            with self.assertRaises(RuntimeError) as context:
                test_object.collect_tests()
                self.assertEqual(context.exception.message,
                                 bad_path + '[\'test8\']')

            mock_path.isabs.return_value = True
            test_object.framework.tests = ['test9/']
            with self.assertRaises(RuntimeError) as context:
                test_object.collect_tests()
                self.assertEqual(context.exception.message,
                                 bad_path + '[\'test9\']')

            test_object.framework.tests = ['test10']
            mock_valid.return_value = False
            with self.assertRaises(RuntimeError) as context:
                test_object.collect_tests()
                self.assertEqual(context.exception.message,
                                 invalid_path + '[\'test10\']')


def walker(test_path, *args, **kwargs):
    # pylint: disable=unused-argument
    yield (test_path, [''], ['test_file', 'test_file.fmt'])
    yield (test_path, [''], ['test_file'])
