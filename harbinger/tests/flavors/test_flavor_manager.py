import argparse
import unittest

import mock
from testfixtures import log_capture

from harbinger.base import Base
from harbinger.flavors.flavor_manager import FlavorManager


class TestFlavorManager(unittest.TestCase):

    def setUp(self):
        self.openstack_creds = {
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
        self.args = mock.Mock(spec=argparse.Namespace)
        self.base_object = Base(app=mock.Mock(), app_args=self.args)
        self.test_object = FlavorManager("framework", **self.openstack_creds)

    @log_capture()
    def test__init(self, capture):
        with mock.patch('harbinger.flavors.flavor_manager.FlavorManager'):
            FlavorManager("framework", **self.openstack_creds)

            capture.check_present(
                ('harbinger.flavors.flavor_manager', 'INFO',
                 'Creating Nova client for framework '
                 'using keystone: test_auth_url')
            )

    @log_capture()
    def test_check_flavor(self, capture):
        self.test_object.nova = mock.MagicMock()

        retval = [mock.MagicMock() for m in range(10)]

        for i, mock_obj in enumerate(retval):
            type(mock_obj).name = mock.PropertyMock(return_value='f' + str(i))

        self.test_object.nova.flavors.list.return_value = retval

        self.assertTrue(self.test_object.check_flavor('f1'))
        self.assertTrue(self.test_object.check_flavor('f6'))
        self.assertFalse(self.test_object.check_flavor('f10'))
        self.assertFalse(self.test_object.check_flavor('f38439'))

        capture.check(
            ('harbinger.flavors.flavor_manager',
             'INFO', 'Flavor <f1> exists: True'),
            ('harbinger.flavors.flavor_manager',
             'INFO', 'Flavor <f6> exists: True'),
            ('harbinger.flavors.flavor_manager',
             'INFO', 'Flavor <f10> exists: False'),
            ('harbinger.flavors.flavor_manager',
             'INFO', 'Flavor <f38439> exists: False')
        )

    @log_capture()
    def test_create_flavor(self, capture):
        self.test_object.nova = mock.MagicMock(autospec=True)
        self.test_object.create_flavor('f1', '2048', '4', '1')
        capture.check(
            ('harbinger.flavors.flavor_manager', 'INFO',
             'Creating flavor f1')
        )
        self.test_object.nova.flavors.create.assert_called_once()
