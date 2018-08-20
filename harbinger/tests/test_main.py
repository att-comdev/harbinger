# Copyright 2018 AT&T Intellectual Property.  All other rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import mock

from harbinger import main
from harbinger.tests import base


class TestMain(base.TestCase):
    @mock.patch('harbinger.main.CommandManager')
    @mock.patch('harbinger.main.App.__init__', autospec=True)
    @mock.patch('harbinger.main.__version__', 'version')
    def test_main_class_init(self, mock_init, mock_command_manager_class):
        mock_command_manager_class.return_value = 'mock command'
        mock_load_commands = mock.Mock()

        def init_side_effect(mock_self, **kwargs):
            expected_kwargs = {
                'command_manager': 'mock command',
                'deferred_help': True,
                'description': 'Manager for Data Plane Testing Frameworks',
                'version': 'version'
            }
            self.assertDictEqual(kwargs, expected_kwargs)

            mock_command_manager = mock.Mock(load_commands=mock_load_commands)
            mock_self.command_manager = mock_command_manager

        mock_init.side_effect = init_side_effect

        main.Harbinger()

        mock_command_manager_class.assert_called_once_with(
            'harbinger.commands')

    @mock.patch('harbinger.main.Harbinger',
                spec=main.Harbinger)
    @mock.patch('harbinger.main.harbingeropts')
    @mock.patch('harbinger.main.logging.setup')
    def test_main(self, mock_logging, mock_harbingeropts, mock_main_class):
        mock_logging.return_value = 1
        mock_harbingeropts.return_value = 1

        mock_main_class.return_value.run.return_value = 17

        self.assertEqual(main.main(['first', 'second', 'third']), 17)

        mock_main_class.return_value.run.assert_called_once_with(['first',
                                                                  'second',
                                                                  'third'])
