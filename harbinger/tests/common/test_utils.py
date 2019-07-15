import os
import unittest

import mock

from oslo_config import cfg

from harbinger.common.utils import Utils
from harbinger.factory.base import BaseFactory


class TestUtils(unittest.TestCase):
    """Unit tests for Utils"""
    def test_load_class(self):
        mock_module = mock.MagicMock()
        mock_module.test_classname = "test_classname"
        with mock.patch.dict('sys.modules', test_module=mock_module):
            self.assertEqual('test_classname',
                             Utils.load_class('test_module.test_classname'))

    def test_load_class_import_error(self):
        def throw(*args, **kwargs):
            # pylint: disable=unused-argument
            # These arguments are used by the call to __import__
            raise ImportError()

        with mock.patch('builtins.__import__', side_effect=throw):
            with self.assertRaises(ImportError):
                Utils.load_class('test.class.please.ignore')

    def test_load_class_attribute_error(self):
        class Stateless():
            pass

        mock_module = mock.MagicMock(spec=Stateless)
        with mock.patch.dict('sys.modules', test_module=mock_module):
            with self.assertRaises(AttributeError):
                Utils.load_class('test_module.test_classname')

    def test_load_class_not_none(self):
        self.assertRaises(ValueError, Utils.load_class, None)

    @mock.patch('oslo_config.cfg.CONF.get')
    @mock.patch('os.path.dirname', return_value='test_path')
    @mock.patch('os.listdir', return_value=['second.py', 'first.py'])
    def test_get_supported_frameworks(self, mock_listdir, mock_dirname,
                                      mock_conf):
        self.assertEqual(['first', 'second'], Utils.get_supported_frameworks())
        self.assertEqual(mock_dirname.call_count, 2)
        self.assertEqual(mock_conf.call_count, 2)
        self.assertEqual(mock_listdir.call_count, 1)

    @mock.patch('os.path.dirname', return_value='test_path')
    @mock.patch('os.listdir', return_value=['second.py', 'first.py'])
    def test_get_supported_frameworks_nosuchopt(self, mock_listdir,
                                                mock_dirname):
        self.assertEqual([], Utils.get_supported_frameworks())
        self.assertEqual(mock_dirname.call_count, 2)
        self.assertEqual(mock_listdir.call_count, 1)

    @mock.patch('harbinger.common.utils.CONF')
    @mock.patch('harbinger.executors.base.BaseExecutor')
    def test_hierarchy_lookup_dict(self, mock_executor, mock_conf):
        mock_executor.options = mock.MagicMock(spec=dict)
        mock_executor.options.get = mock.MagicMock(return_value='test_val')
        self.assertEqual(Utils.hierarchy_lookup(mock_executor, 'test_key'),
                         'test_val')
        self.assertEqual(mock_conf.call_count, 0)

    @mock.patch('harbinger.common.utils.CONF')
    @mock.patch('harbinger.executors.base.BaseExecutor')
    def test_hierarchy_lookup_basefactory(self, mock_executor, mock_conf):
        mock_executor.options = mock.MagicMock(spec=BaseFactory)
        mock_executor.options.test_attr = 'test_val'
        self.assertEqual(Utils.hierarchy_lookup(mock_executor, 'test_attr'),
                         'test_val')
        self.assertEqual(mock_conf.call_count, 0)

    @mock.patch('harbinger.common.utils.CONF')
    @mock.patch('harbinger.executors.base.BaseExecutor')
    def test_hierarchy_lookup_groupattr(self, mock_executor, mock_conf):
        mock_executor.options = mock.MagicMock(spec=dict)
        mock_executor.options.get = mock.MagicMock(
            return_value='test low priority')
        mock_executor.framework.required = mock.MagicMock(spec=dict)
        mock_executor.framework.required.get = mock.MagicMock(
            return_value='test high priority')
        self.assertEqual(Utils.hierarchy_lookup(mock_executor, 'test_key'),
                         'test high priority')
        self.assertEqual(mock_conf.call_count, 0)

    @mock.patch('harbinger.common.utils.CONF')
    @mock.patch('harbinger.executors.base.BaseExecutor')
    def test_hierarchy_lookup_priorty(self, mock_executor, mock_conf):
        mock_executor.options = mock.MagicMock(spec=cfg.ConfigOpts.GroupAttr)
        mock_executor.options.test_attr = 'test_val'
        self.assertEqual(Utils.hierarchy_lookup(mock_executor, 'test_attr'),
                         'test_val')
        self.assertEqual(mock_conf.call_count, 0)

    @mock.patch.object(os._Environ, '__setitem__')
    @mock.patch.object(Utils, 'hierarchy_lookup')
    def test_source_openrc(self, mock_hierarchy, mock_setitem):
        mock_hierarchy.side_effect = [
            'username', 'password', 'project_name', 'external_network'
        ]
        Utils.source_openrc(None)
        self.assertEqual(mock_hierarchy.call_count, 4)
        self.assertEqual(mock_setitem.call_count, 4)
