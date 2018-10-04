import unittest

import mock

from harbinger.common.utils import Utils
from harbinger.executors.shaker import ShakerExecutor


class TestShakerExecutor(unittest.TestCase):

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
                mock_lookup.return_value = 'foo'
                with mock.patch.object(ShakerExecutor,
                                       'format_collected_tests'):
                    with mock.patch.object(ShakerExecutor, 'collect_tests'):
                        test_object = ShakerExecutor(
                            self.mock_framework,
                            self.mock_environment,
                            self.mock_options
                        )
        test_object.image = mock.Mock()
        test_object.config = mock.Mock()
        return test_object

    def test___init__(self):
        test_object = self._get_test_object()

        self.assertEqual(test_object.cfg_file_name,
                         'test_framework_name.cfg')
        self.assertEqual(test_object.cfg_full_path,
                         'test_files_dir/inputs/test_framework_name.cfg')
        self.assertEqual(test_object.results_json_path,
                         'test_files_dir/outputs/shaker-results.json')

    @mock.patch.object(ShakerExecutor, '_exec_cmd')
    @mock.patch.object(ShakerExecutor, 'create_cfg_file')
    @mock.patch.object(ShakerExecutor, 'create_image')
    @mock.patch('harbinger.common.utils.Utils.hierarchy_lookup',
                return_value='test_image')
    @mock.patch('harbinger.executors.base.BaseExecutor.setup')
    def test_setup(self, mock_base_setup, mock_hierarchy_lookup,
                   mock_create_image, mock_create_cfg_file,
                   mock_exec_cmd):
        test_object = self._get_test_object()
        test_object.image.check_image = mock.Mock(return_value=False)
        test_object.image.upload_image = mock.Mock()
        test_object.setup()

        mock_base_setup.assert_called()
        mock_hierarchy_lookup.assert_called_once_with(test_object, 'image')
        mock_create_image.assert_called_once()
        test_object.image.upload_image.assert_called_once_with(
            'test_image', 'qcow2', 'bare'
        )
        mock_create_cfg_file.assert_called_once()
        mock_exec_cmd.assert_called_once_with(
            "shaker --config-file test_files_dir/"
            "inputs/test_framework_name.cfg"
        )

        test_object.image.check_image = mock.Mock(return_value=True)
        test_object.setup()
        mock_create_image.assert_called_once()
        test_object.image.upload_image.assert_called_once_with(
            'test_image', 'qcow2', 'bare'
        )

    def test_add_extras_values(self):
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

    def test_format_collected_tests(self):
        test_object = self._get_test_object()
        tests = ['test1', 'test2', 'test3']
        self.assertEqual(
            test_object.format_collected_tests(tests),
            "test1, test2, test3, "
        )

    @mock.patch.object(ShakerExecutor, 'add_extras_options')
    def test_create_cfg_file(self, mock_add_extras_options):
        test_object = self._get_test_object()
        test_object.results_json_path = "test_output"
        test_object.formated_tests = "test_scenario"

        def mock_hierarchy_lookup(obj, attr):
            # pylint: disable=unused-argument
            return 'test_' + attr

        with mock.patch('harbinger.common.utils.Utils.hierarchy_lookup',
                        side_effect=mock_hierarchy_lookup):
            mock_open = mock.mock_open()
            open_name = 'harbinger.executors.shaker.open'
            with mock.patch(open_name, mock_open, create=True):
                test_object.create_cfg_file()

        mock_add_extras_options.assert_called_once()
        calls = [
            mock.call('DEFAULT', 'os_username', 'test_username'),
            mock.call('DEFAULT', 'os_password', 'test_password'),
            mock.call('DEFAULT', 'os_project_name', 'test_project'),
            mock.call('DEFAULT', 'flavor_name', 'test_flavor_name'),
            mock.call('DEFAULT', 'image_name', 'test_image'),
            mock.call('DEFAULT', 'output', 'test_output'),
            mock.call('DEFAULT', 'scenario', 'test_scenario'),
            mock.call('DEFAULT', 'server_endpoint', 'test_server_endpoint'),
            mock.call('DEFAULT', 'external_net', 'test_external_network')
        ]
        test_object.config.set.assert_has_calls(calls)

    @mock.patch('harbinger.common.utils.Utils.source_openrc')
    @mock.patch.object(ShakerExecutor, '_exec_cmd')
    def test_create_image(self, mock_exec_cmd, mock_source_openrc):
        test_object = self._get_test_object()
        test_object.create_image()
        mock_source_openrc.assert_called_once_with(test_object)
        mock_exec_cmd.assert_called_once_with('shaker-image-builder')
