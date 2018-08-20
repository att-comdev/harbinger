"""
Options class:
    - Stores all framework options into lists and dicts respectively
"""

from harbinger.factory.base import BaseFactory


class Options(BaseFactory):
    def __init__(self, options):
        super(Options, self).__init__()
        for item in options:
            setattr(self, item, options[item])
