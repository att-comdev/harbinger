import logging
import os
import sys

ATTRIBUTES = dict(
    list(zip([
        'bold',
        'dark',
        '',
        'underline',
        'blink',
        '',
        'reverse',
        'concealed'
        ],
        list(range(1, 9))
        ))
    )
del ATTRIBUTES['']


HIGHLIGHTS = dict(
    list(zip([
        'on_grey',
        'on_red',
        'on_green',
        'on_yellow',
        'on_blue',
        'on_magenta',
        'on_cyan',
        'on_white'
        ],
        list(range(40, 48))
        ))
    )


COLORS = dict(
    list(zip([
        'grey',
        'red',
        'green',
        'yellow',
        'blue',
        'magenta',
        'cyan',
        'white',
        ],
        list(range(30, 38))
        ))
    )


RESET = '\033[0m'
DEFAULT_FMT = ('%(asctime)s.%(msecs)03d %(processName)s ' +
               '%(levelname)s %(name)s [-] %(message)s')


class ColorLogFormatter(logging.Formatter):
    # ======================================
    # This file is the result of multiple
    # sleepless nights and early mornings
    # and numerous Google searches
    # ======================================

    level_colors = {
        logging.DEBUG: 'cyan',
        logging.INFO: 'green',
        logging.WARNING: 'yellow',
        logging.ERROR: 'red',
        logging.CRITICAL: 'red',
    }

    def __init__(self):
        # =============================================
        # Set the logging message format
        # and the date format to make the message
        # human readable
        # =============================================
        datefmt = '%Y-%m-%d %H:%M:%S'
        super(ColorLogFormatter, self).__init__(DEFAULT_FMT, datefmt)

    def _get_exc_info(self, record):
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            try:
                return unicode(record.exc_text)
            except UnicodeError:
                # Sometimes filenames have non-ASCII chars, which can lead
                # to errors when s is Unicode and record.exc_text is str
                # See issue 8924.
                # We also use replace for when there are multiple
                # encodings, e.g. UTF-8 for the filesystem and latin-1
                # for a script. See issue 13232.
                return record.exc_text.decode(sys.getfilesystemencoding(),
                                              'replace')
        return None

    def format(self, record):
        # ===============================================
        # This is the main method whereby the log
        # messages are colored to have a rainbow effect
        # ===============================================

        # provides a way to strip out color and log format for a "plain" entry
        if hasattr(record, 'plainOutput'):
            if record.plainOutput is True:
                self._fmt = '%(message)s'
        else:
            self._fmt = DEFAULT_FMT
            color = self.level_colors.get(record.levelno, 'white')
            record.color = color
            record.levelname = self.colored(record.levelname, color,
                                            attrs=['bold'])
            record.name = self.colored(record.name, 'red')
            record.message = self.colored(record.getMessage(), color)
            record.msg = self.colored(record.msg, color)

        message = super(ColorLogFormatter, self).format(record)

        exc_info = self._get_exc_info(record)
        if exc_info is not None:
            if message[-1:] != "\n":
                message = message + "\n\n"
            message += self.colored(exc_info, 'grey', attrs=['bold'])

        return message

    def colored(self, text, color=None, on_color=None, attrs=None):
        # ==========================================================
        # Colorize the text
        # --------------------------------------------------------
        # Available text colors:
        #     red, green, yellow, blue, magenta, cyan, white.
        # --------------------------------------------------------
        # Available text highlights:
        #     on_red, on_green, on_yellow, on_blue,
        #     on_magenta, on_cyan, on_white.
        # --------------------------------------------------------
        # Available attributes:
        #     bold, dark, underline, blink, reverse, concealed.
        # --------------------------------------------------------
        # Example:
        #     self.colored('Hello, World!', 'red', 'on_grey',
        #                  ['blue', 'blink'])
        #     self.colored('Hello, World!', 'green')
        # --------------------------------------------------------
        # ==========================================================
        if os.getenv('ANSI_COLORS_DISABLED') is None:
            fmt_str = '\033[%dm%s'
            if color is not None:
                text = fmt_str % (COLORS[color], text)

            if on_color is not None:
                text = fmt_str % (HIGHLIGHTS[on_color], text)

            if attrs is not None:
                for attr in attrs:
                    text = fmt_str % (ATTRIBUTES[attr], text)

            text += RESET
        return text
