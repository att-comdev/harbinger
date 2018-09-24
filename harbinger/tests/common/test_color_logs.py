# This Python file uses the following encoding: utf-8
#
# Copyright 2018 Accenture
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import os
import unittest
import uuid

from testfixtures import log_capture

from harbinger.common import color_logs


class ColorLogFormatterTest(unittest.TestCase):

    def setUp(self):
        self.formatter = color_logs.ColorLogFormatter()

    @log_capture()
    def test_format(self, l):
        message = "Testing message %s." % uuid.uuid4().hex
        logger = logging.getLogger()
        logger.info(message)

        self.assertNotEqual(message, self.formatter.format(l.records[0]))
        self.assertIn(message, self.formatter.format(l.records[0]))

    @log_capture()
    def test_format_plain_output(self, l):
        message = "Testing message %s." % uuid.uuid4().hex
        logger = logging.getLogger()
        logger.info(message)

        setattr(l.records[0], "plainOutput", True)
        # FIXME(lamt): There is a bug where this plain output does not work
        # properly, once that is fixed we should be replacing assertIn with
        # assertEqual as that's the correct thing here.
        self.assertIn(message, self.formatter.format(l.records[0]))

    @log_capture()
    def test_format_with_exception(self, l):
        message = "Testing exception with non ascii char"
        logger = logging.getLogger()
        try:
            raise ValueError(message)
        except ValueError as e:
            logger.exception(e, exc_info=True)

        # We will zero out exc_text to test the condition
        setattr(l.records[0], "exc_text", None)

        # TODO(lamt): We should add in additional asserts for better
        # testing of this test scenario.
        self.assertIn(message, self.formatter.format(l.records[0]))

        # Test unicode errors
        setattr(l.records[0], "exc_text", "caf仪")

        # TODO(lamt): We should add in additional asserts for better
        # testing of this test scenario.
        self.assertIn(message, self.formatter.format(l.records[0]))

    def test_colored_with_ansi_coloring_enabled(self):
        text = uuid.uuid4().hex
        os.environ.pop('ANSI_COLORS_DISABLED', None)

        self.assertEqual("%s%s" % (text, color_logs.RESET),
                         self.formatter.colored(text))
        self.assertEqual("%s%s%s" % ('\033[4m\033[5m\033[41m\033[34m',
                                     text, color_logs.RESET),
                         self.formatter.colored(
                             text,
                             color="blue",
                             on_color="on_red",
                             attrs=["blink", "underline"]))

    def test_colored_with_ansi_coloring_disabled(self):
        # If we disable Ansi-coloring, the input string should be the same
        # as the output string regardless of the inputs.
        text = uuid.uuid4().hex
        expected = text

        os.environ['ANSI_COLORS_DISABLED'] = "Y"
        self.assertEqual(expected, self.formatter.colored(text))
        self.assertEqual(expected,
                         self.formatter.colored(
                             text,
                             color="blue",
                             on_color="on_red",
                             attrs=["blink", "underline"]))

        os.environ.pop('ANSI_COLORS_DISABLED', None)
