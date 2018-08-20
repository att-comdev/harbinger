"""
Environment class:
    - Stores all environment options into variables to be
     accesses by other classes
"""

from harbinger.factory.base import BaseFactory


class Environment(BaseFactory):
    def __init__(self, environment):
        super(Environment, self).__init__()
        for item in environment:
            setattr(self, item, environment[item])
