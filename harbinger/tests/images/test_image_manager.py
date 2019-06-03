import unittest

import mock
from testfixtures import log_capture

from harbinger.images.image_manager import ImageManager


class TestImageManager(unittest.TestCase):

    def _get_test_object(self):
        openstack_creds = {
            'auth_url': 'test_auth_url',
            'user_id': 'test_user_id',
            'username': 'test_username',
            'password': 'test_password',  # nosec
            'user_domain_id': 'test_user_domain_id',
            'user_domain_name': 'test_user_domain_name',
            'project_id': 'test_project_id',
            'project_name': 'test_project_name',
            'project_domain_id': 'test_project_domain_id',
            'project_domain_name': 'test_project_domain_name'
        }
        with mock.patch('keystoneauth1.loading.get_plugin_loader'):
            with mock.patch('harbinger.images.image_manager.Client'):
                with mock.patch('keystoneauth1.session.Session'):
                    test_label = 'test_label'

                    return ImageManager(test_label, **openstack_creds)

    @log_capture()
    def test___init__(self, capture):
        test_object = self._get_test_object()  # noqa: F841
        capture.check(
            ('harbinger.images.image_manager', 'INFO',
             'Creating Glance client for test_label '
             'using keystone: test_auth_url'),
        )

    @log_capture()
    def test_check_image(self, capture):
        test_object = self._get_test_object()
        test_object.glance.images.list.side_effect = [
            [{'name': 'test_image1'}, {'name': 'test_image2'}]
        ]
        self.assertFalse(test_object.check_image('test_image_name'))
        capture.check_present(
            ('harbinger.images.image_manager', 'INFO',
             'Image <test_image_name> exists in Glance: False'),
        )
        test_object.glance.images.list.side_effect = [
            [{'name': 'test_image1'}, {'name': 'test_image_name'}]
        ]
        self.assertTrue(test_object.check_image('test_image_name'))
        capture.check_present(
            ('harbinger.images.image_manager', 'INFO',
             'Image <test_image_name> exists in Glance: True'),
        )

    @log_capture()
    def test_upload_image_success(self, capture):
        test_object = self._get_test_object()
        with mock.patch('harbinger.images.image_manager.CONF') as mock_conf:
            mock_conf.DEFAULT.files_dir = 'test_dir'
            with mock.patch('os.listdir') as mock_listdir:
                mock_listdir.side_effect = [
                    ['wrong_file', 'test_image_name'],
                ]
                mock_open = mock.mock_open()
                open_name = 'harbinger.images.image_manager.open'
                with mock.patch(open_name, mock_open, create=True):
                    test_object.upload_image('test_image_name',
                                             'test_disk_format',
                                             'test_container_format')
                    test_object.glance.images.create.assert_called()
                    test_object.glance.images.upload.assert_called()
                    capture.check_present(
                        ('harbinger.images.image_manager',
                         'INFO',
                         'Uploading image <test_image_name> into Glance....'),
                        ('harbinger.images.image_manager',
                         'INFO',
                         'Image <test_image_name> uploaded into Glance'),
                    )

    def test_upload_image_missing_file(self):
        test_object = self._get_test_object()
        with mock.patch('harbinger.images.image_manager.CONF') as mock_conf:
            mock_conf.DEFAULT.files_dir = 'test_dir'
            with mock.patch('os.listdir') as mock_listdir:
                mock_listdir.side_effect = [
                    ['wrong_file', 'another_wrong_file'],
                ]
                with self.assertRaises(OSError) as context:
                    test_object.upload_image('test_image_name',
                                             'test_disk_format',
                                             'test_container_format')
                    exception = context.exception
                    self.assertEqual(exception.message,
                                     'Image upload error: test_image_name '
                                     'could not be found in test_dir/images')

    @log_capture()
    def test_upload_image_glance_error(self, capture):
        test_object = self._get_test_object()
        with mock.patch('harbinger.images.image_manager.CONF') as mock_conf:
            mock_conf.DEFAULT.files_dir = 'test_dir'
            with mock.patch('os.listdir') as mock_listdir:
                mock_listdir.side_effect = [
                    ['wrong_file', 'test_image_name'],
                ]
                mock_open = mock.mock_open()
                open_name = 'harbinger.images.image_manager.open'
                with mock.patch(open_name, mock_open, create=True):
                    test_object.glance.images.upload.side_effect = OSError(
                        'test_exception')
                    with self.assertRaises(OSError):
                        test_object.upload_image('test_image_name',
                                                 'test_disk_format',
                                                 'test_container_format')
                        test_object.glance.images.create.assert_called()
                        test_object.glance.images.upload.assert_called()
                        capture.check_present(
                            ('harbinger.images.image_manager',
                             'INFO',
                             'Uploading image <test_image_name> '
                             'into Glance....'),
                            ('harbinger.images.image_manager',
                             'ERROR',
                             'Error connecting to Glance, check proxy and '
                             'no_proxy settings\ntest_exception'),
                        )
