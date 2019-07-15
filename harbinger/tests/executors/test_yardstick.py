import os
import tempfile
import unittest

import mock

from harbinger.common.utils import Utils
from harbinger.executors.yardstick import YardstickExecutor


class TestYardstickExecutor(unittest.TestCase):
    def setUp(self):
        self.mock_framework = mock.Mock()
        self.mock_framework.name = 'test_framework_name'

        self.mock_environment = mock.Mock()
        self.mock_environment.OS_AUTH_URL = 'test_os_auth_url'
        self.mock_environment.OS_API_VERSION = 'test_os_api_version'

        self.mock_options = mock.Mock()

        self.temp_dir = tempfile.gettempdir()

    def _get_test_object(self):
        with mock.patch('harbinger.executors.base.CONF') as mock_conf:
            mock_conf.DEFAULT.files_dir = 'test_files_dir'

            with mock.patch.object(Utils, 'hierarchy_lookup') as mock_lookup:
                mock_lookup.return_value = 'test_paths'
                with mock.patch('harbinger.executors.'
                                'yardstick.CONF') as mock_conf2:
                    mock_conf2['test_framework_name'].test_paths = 'test_paths'
                    with mock.patch.object(YardstickExecutor,
                                           'format_collected_tests'):
                        with mock.patch.object(YardstickExecutor,
                                               'collect_tests'):
                            test_object = YardstickExecutor(
                                self.mock_framework, self.mock_environment,
                                self.mock_options)
        test_object.image = mock.Mock()
        test_object.flavor = mock.Mock()
        test_object.config = mock.Mock()
        return test_object

    def test___init__(self):
        test_object = self._get_test_object()
        self.assertEqual(test_object.outputs_full_path,
                         'test_files_dir/outputs/yardstick.out')
        self.assertEqual(test_object.inputs_dir, 'test_files_dir/inputs')
        self.assertEqual(
            test_object.relative_path, 'test_files_dir/frameworks/'
            'test_framework_name/test_paths')
        self.assertEqual(test_object.outputs_dir, 'test_files_dir/outputs')
        self.assertEqual(test_object.test_suite_name, 'yardstick-suite.yaml')
        self.assertEqual(test_object.test_paths, 'test_paths')
        self.assertEqual(test_object.conf_file_name,
                         'test_framework_name.conf')
        self.assertEqual(test_object.conf_full_path,
                         'test_files_dir/inputs/test_framework_name.conf')

    @mock.patch.object(YardstickExecutor, '_exec_cmd')
    @mock.patch.object(YardstickExecutor, 'create_test_suite')
    @mock.patch.object(YardstickExecutor, 'create_yardstick_conf')
    @mock.patch.object(YardstickExecutor, 'create_image')
    @mock.patch('harbinger.common.utils.Utils.source_openrc')
    @mock.patch('harbinger.common.utils.Utils.hierarchy_lookup')
    @mock.patch('harbinger.executors.base.BaseExecutor.setup')
    def test_setup_positives(self, mock_base_setup, mock_hierarchy_lookup,
                             mock_source_openrc, mock_create_image,
                             mock_create_yardstick_conf,
                             mock_create_test_suite, mock_exec_cmd):
        test_object = self._get_test_object()
        mock_hierarchy_lookup.side_effect = [
            'test_flavor_name', 'test_image_name'
        ]
        test_object.flavor.check_flavor.return_value = False
        test_object.image.check_image.return_value = False
        test_object.setup()

        mock_base_setup.assert_called_once()
        test_object.flavor.check_flavor.assert_called_once_with(
            'test_flavor_name')
        test_object.flavor.create_flavor.assert_called_once_with(
            name='test_flavor_name',
            ram='512',
            vcpus='1',
            disk='3',
            swap='100')
        test_object.image.check_image.assert_called_once_with(
            'test_image_name')
        mock_create_image.assert_called_once()
        test_object.image.upload_image.assert_called_once_with(
            'test_image_name', 'qcow2', 'bare',
            self.temp_dir + '/workspace/yardstick/')
        mock_create_yardstick_conf.assert_called_once()
        mock_create_test_suite.assert_called_once()
        mock_source_openrc.assert_called_once_with(test_object)
        mock_exec_cmd.assert_called_once_with(
            'yardstick --config-file test_files_dir/inputs/'
            'test_framework_name.conf task start --output-file '
            'test_files_dir/outputs/yardstick.out --suite '
            'test_files_dir/inputs/yardstick-suite.yaml')

    @mock.patch.object(YardstickExecutor, '_exec_cmd')
    @mock.patch.object(YardstickExecutor, 'create_test_suite')
    @mock.patch.object(YardstickExecutor, 'create_yardstick_conf')
    @mock.patch.object(YardstickExecutor, 'create_image')
    @mock.patch('harbinger.common.utils.Utils.source_openrc')
    @mock.patch('harbinger.common.utils.Utils.hierarchy_lookup')
    @mock.patch('harbinger.executors.base.BaseExecutor.setup')
    def test_setup_negatives(self, mock_base_setup, mock_hierarchy_lookup,
                             mock_source_openrc, mock_create_image,
                             mock_create_yardstick_conf,
                             mock_create_test_suite, mock_exec_cmd):
        test_object = self._get_test_object()
        mock_hierarchy_lookup.side_effect = [
            'test_flavor_name', 'test_image_name'
        ]
        test_object.flavor.check_flavor.return_value = True
        test_object.image.check_image.return_value = True
        test_object.setup()

        mock_base_setup.assert_called_once()
        test_object.flavor.check_flavor.assert_called_once_with(
            'test_flavor_name')
        test_object.flavor.create_flavor.assert_not_called()
        test_object.image.check_image.assert_called_once_with(
            'test_image_name')
        mock_create_image.assert_not_called()
        test_object.image.upload_image.assert_not_called()
        mock_create_yardstick_conf.assert_called_once()
        mock_create_test_suite.assert_called_once()
        mock_source_openrc.assert_called_once_with(test_object)
        mock_exec_cmd.assert_called_once_with(
            'yardstick --config-file test_files_dir/inputs/'
            'test_framework_name.conf task start --output-file '
            'test_files_dir/outputs/yardstick.out --suite '
            'test_files_dir/inputs/yardstick-suite.yaml')

    def test_format_collected_tests(self):
        test_object = self._get_test_object()
        tests = ['xtest1', 'xtest2', 'xtest3']
        self.assertEqual(test_object.format_collected_tests(tests), [
            {
                'file_name': 'test1'
            },
            {
                'file_name': 'test2'
            },
            {
                'file_name': 'test3'
            },
        ])

    @mock.patch('harbinger.common.utils.Utils.hierarchy_lookup')
    def test_create_test_suite_positive(self, mock_lookup):
        test_object = self._get_test_object()
        mock_lookup.return_value = 'test_schema'
        test_list = [{'file_name': 'test1'}]
        mock_open = mock.mock_open()
        open_name = 'harbinger.executors.yardstick.open'
        with mock.patch(open_name, mock_open, create=True):
            test_object.create_test_suite(test_list)
        handle = mock_open()
        handle.write.assert_called_once_with('schema: test_schema\n'
                                             'name: yardstick-suite.yaml\n'
                                             'test_cases_dir: test_paths\n'
                                             'test_cases:\n'
                                             '- file_name: test1\n')

    @mock.patch('harbinger.common.utils.Utils.hierarchy_lookup')
    def test_create_test_suite_negative(self, mock_lookup):
        test_object = self._get_test_object()
        mock_lookup.return_value = 'test_schema'
        test_list = [{'file_name': 'test_paths/test1'}]
        mock_open = mock.mock_open()
        open_name = 'harbinger.executors.yardstick.open'
        with mock.patch(open_name, mock_open, create=True):
            test_object.create_test_suite(test_list)
        handle = mock_open()
        handle.write.assert_called_once_with('schema: test_schema\n'
                                             'name: yardstick-suite.yaml\n'
                                             'test_cases_dir: /\n'
                                             'test_cases:\n'
                                             '- file_name: test_paths/test1\n')

    def test_add_extras_options(self):
        test_object = self._get_test_object()
        test_object.framework.extras = {
            'key1': 'val1',
            'key2': 'val2',
            'key3': 'val3',
        }
        test_object.add_extras_options()
        calls = [
            mock.call('DEFAULT', 'key1', 'val1'),
            mock.call('DEFAULT', 'key2', 'val2'),
            mock.call('DEFAULT', 'key3', 'val3'),
        ]
        test_object.config.set.assert_has_calls(calls, any_order=True)

    @mock.patch.object(YardstickExecutor, 'add_extras_options')
    def test_create_yardstick_conf(self, mock_add_extras_options):
        test_object = self._get_test_object()
        test_object.framework.extras = ['extras']

        def mock_hierarchy_lookup(obj, attr):
            # pylint: disable=unused-argument
            return 'test_' + attr

        with mock.patch('harbinger.common.utils.Utils.hierarchy_lookup',
                        side_effect=mock_hierarchy_lookup):
            mock_open = mock.mock_open()
            open_name = 'harbinger.executors.yardstick.open'
            with mock.patch(open_name, mock_open, create=True):
                test_object.create_yardstick_conf()

        mock_add_extras_options.assert_called_once()
        calls = [
            mock.call('DEFAULT', 'debug', 'test_debug'),
            mock.call('DEFAULT', 'dispatcher', 'test_dispatcher'),
            mock.call('dispatcher_file', 'file_name',
                      'test_files_dir/outputs/test_dispatcher_file_name'),
            mock.call('DEFAULT', 'debug', 'test_debug'),
        ]
        test_object.config.set.assert_has_calls(calls)
        test_object.config.add_section.assert_called_once_with(
            'dispatcher_file')
        test_object.config.write.assert_called_once()

    @mock.patch('harbinger.common.utils.Utils.source_openrc')
    @mock.patch.object(YardstickExecutor, '_exec_cmd')
    def test_create_image(self, mock_exec_cmd, mock_source_openrc):
        test_object = self._get_test_object()
        with mock.patch('harbinger.executors.yardstick.CONF') as mock_conf:
            mock_conf.DEFAULT.files_dir = 'test_files_dir'
            with mock.patch.dict(os.environ, {}, clear=True):
                test_object.create_image()
                self.assertTrue(len(os.environ) == 1)
                self.assertIn('YARD_IMG_ARCH', os.environ)
                self.assertEqual('amd64', os.environ['YARD_IMG_ARCH'])
        mock_exec_cmd.assert_called_once_with(
            'apt update && '
            'test_files_dir/frameworks/yardstick/tools/yardstick-img-modify '
            'test_files_dir/frameworks/yardstick/tools/'
            'ubuntu-server-cloudimg-modify.sh')
        mock_source_openrc.assert_called_once_with(test_object)
