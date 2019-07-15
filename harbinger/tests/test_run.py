import argparse
import signal
import unittest

import mock
from testfixtures import log_capture

from harbinger.run import loader
from harbinger.run import Run
from harbinger.run import worker
from harbinger.run import worker_init


class TestRun(unittest.TestCase):
    def setUp(self):
        self.args = mock.Mock(spec=argparse.Namespace)
        self.args.yaml_file = 'test_yaml'
        self.test_object = Run(app=mock.Mock(), app_args=self.args)
        self.test_object.framework_extractor = mock.Mock()
        self.test_object.environment_extractor = mock.Mock()
        self.test_object.options_extractor = mock.Mock()

    def test_get_description(self):
        self.assertEqual(self.test_object.get_description(),
                         'run harbinger by providing a yaml file')

    def test_get_parser(self):
        parser = self.test_object.get_parser('NAME')
        self.assertEqual('NAME', parser.prog)

    def test_parse_frameworks(self):
        short_fn = self.test_object.framework_extractor.parse_frameworks
        short_fn.return_value = 'test_framework'
        self.test_object.parse_frameworks()
        self.assertEqual(self.test_object.frameworks_dict, 'test_framework')

    def test_parse_environment(self):
        short_fn = self.test_object.environment_extractor.parse_environment
        short_fn.return_value = 'test_environment'
        self.test_object.parse_environment()
        self.assertEqual(self.test_object.environment, 'test_environment')

    def test_parse_options(self):
        short_fn = self.test_object.options_extractor.parse_options
        short_fn.return_value = 'test_options'
        self.test_object.parse_options()
        self.assertEqual(self.test_object.options, 'test_options')

    @mock.patch.object(Run, 'begin')
    @mock.patch.object(Run, 'parse_options')
    @mock.patch.object(Run, 'parse_environment')
    @mock.patch.object(Run, 'parse_frameworks')
    @mock.patch('harbinger.run.OptionsExtractor')
    @mock.patch('harbinger.run.EnvironmentExtractor')
    @mock.patch('harbinger.run.FrameworkExtractor')
    @mock.patch.object(Run, 'load_yaml')
    @mock.patch('harbinger.run.DirectoryManager')
    def test_take_action(self, mock_dir_manager, mock_load_yaml,
                         mock_framework_extractor, mock_env_extractor,
                         mock_options_extractor, mock_parse_frameworks,
                         mock_parse_envs, mock_parse_opts, mock_begin):
        parsed_args = mock.Mock(spec=argparse.Namespace)
        parsed_args.yaml = 'test_yaml'
        self.test_object.take_action(parsed_args)

        mock_dir_manager.assert_called_once()
        mock_load_yaml.assert_called_once_with('test_yaml')
        mock_framework_extractor.assert_called_once()
        mock_env_extractor.assert_called_once()
        mock_options_extractor.assert_called_once()
        mock_parse_frameworks.assert_called_once()
        mock_parse_envs.assert_called_once()
        mock_parse_opts.assert_called_once()
        mock_begin.assert_called_once()

    @mock.patch.object(Run, 'execute_serial')
    @mock.patch('harbinger.run.Core')
    @mock.patch.object(Run, 'load_yaml')
    def test_begin_serial(self, mock_load_yaml, mock_core,
                          mock_execute_serial):
        self.test_object.directory_manager = mock.Mock()
        self.test_object.options = mock.Mock()
        self.test_object.options.execution_mode = 'serial'
        self.test_object.begin()
        mock_load_yaml.assert_called_once()
        mock_core.assert_called_once()
        mock_execute_serial.assert_called_once()

    @mock.patch.object(Run, 'execute_parallel')
    @mock.patch('harbinger.run.Core')
    @mock.patch.object(Run, 'load_yaml')
    def test_begin_parallel(self, mock_load_yaml, mock_core,
                            mock_execute_parallel):
        self.test_object.directory_manager = mock.Mock()
        self.test_object.options = mock.Mock()
        self.test_object.options.execution_mode = 'parallel'
        self.test_object.begin()
        mock_load_yaml.assert_called_once()
        mock_core.assert_called_once()
        mock_execute_parallel.assert_called_once()

    @mock.patch('harbinger.run.worker')
    def test_execute_serial(self, mock_worker):
        self.test_object.frameworks_dict = {'key': 'val'}
        self.test_object.environment = 'test_env'
        self.test_object.options = 'test_options'
        self.test_object.execute_serial()
        mock_worker.assert_called_once_with(
            ['key', 'val', 'test_env', 'test_options'])

    @mock.patch('harbinger.run.worker_init', return_value='worker_id')
    @mock.patch('harbinger.run.multiprocessing.Pool')
    @mock.patch('harbinger.run.os.getpid', return_value='12345')
    def test_execute_parallel(self, mock_getpid, mock_pool, mock_worker_init):
        self.test_object.frameworks_dict = {'key': 'val'}
        self.test_object.environment = 'test_env'
        self.test_object.options = 'test_options'
        self.test_object.execute_parallel()
        mock_getpid.assert_called()
        mock_worker_init.assert_called_once_with('12345')
        mock_pool.assert_called_once_with(initializer='worker_id')

    @mock.patch('harbinger.common.utils.Utils.load_class')
    def test_loader(self, mock_load_class):
        loader('test', 'framework', 'environment', 'options')
        mock_load_class.assert_called_once_with(
            'harbinger.executors.test.TestExecutor')

    @log_capture()
    @mock.patch('harbinger.run.Process')
    def test_worker_init(self, mock_process, capture):
        parent = mock.Mock()
        child1 = mock.Mock()
        child2 = mock.Mock()
        child1.pid = 1
        child2.pid = 2
        parent.children.return_value = [child1, child2]
        mock_process.side_effect = [parent, mock.Mock()]
        self.addCleanup(signal.signal, signal.SIGINT,
                        signal.getsignal(signal.SIGINT))
        # all of the following numbers are arbitrary
        with mock.patch('harbinger.run.signal.signal') as mock_signal:
            mock_signal.side_effect = lambda a, b: b(3, 4)
            with mock.patch('harbinger.run.os.getpid') as mock_getpid:
                mock_getpid.return_value = 2
                worker_init(5)
        child1.kill.assert_called_once()
        child2.kill.assert_not_called()
        parent.kill.assert_called_once()
        capture.check(
            ('harbinger.run', 'ERROR', 'signal: 3 frame: 4'),
            ('harbinger.run', 'ERROR', 'exiting child: 1'),
            ('harbinger.run', 'ERROR', 'exiting parent: 5'),
            ('harbinger.run', 'ERROR', 'exiting all: 2'),
        )

    @mock.patch('harbinger.run.multiprocessing')
    @mock.patch('harbinger.run.loader')
    def test_worker_success(self, mock_loader, mock_multiprocessing):
        worker(['test'])
        mock_loader.assert_called()
        mock_multiprocessing.current_process.assert_called()

    @log_capture()
    @mock.patch('harbinger.run.traceback')
    @mock.patch('harbinger.run.loader')
    def test_worker_failure(self, mock_loader, mock_traceback, capture):
        mock_loader.side_effect = OSError
        with mock.patch('harbinger.run.io') as mock_io:
            mock_exc_buffer = mock.Mock()
            mock_exc_buffer.getvalue.return_value = 'test_string'
            mock_io.StringIO.return_value = mock_exc_buffer
            with mock.patch('harbinger.run.multiprocessing'):
                self.assertRaises(OSError, worker, ['test'])
        mock_loader.assert_called()
        mock_traceback.print_exc.assert_called()
        capture.check(('harbinger.run', 'ERROR', 'test_string'), )
