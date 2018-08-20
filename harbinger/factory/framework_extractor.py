"""
FrameworkExtractor class:
    - extracts all frameworks from the yaml file and passes
    them into the Framework class to be initialized into their
    own framework and placed into a framework list
"""
import collections

from harbinger.factory.framework import Framework


class FrameworkExtractor(object):
    """Initialize all available frameworks provided in the yaml file"""

    def parse_frameworks(self, yaml_file):
        framework_dict = collections.OrderedDict()
        for framework_name in yaml_file["Execute"]:
            framework_dict[framework_name] = Framework(
                yaml_file["Execute"][framework_name], framework_name)

        return framework_dict
