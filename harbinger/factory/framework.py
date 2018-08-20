"""
Framework class:
    - Stores all framework options into lists and dicts respectively
"""

from harbinger.factory.base import BaseFactory


class Framework(BaseFactory):
    def __init__(self, framework, name):
        super(Framework, self).__init__()
        self.name = name
        for item in framework:
            setattr(self, item, framework[item])
