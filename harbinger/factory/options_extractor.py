"""
OptionsExtractor class:
    - extracts Options from the yaml file and passes
    them into the Options class to be initialized
"""

from harbinger.factory.options import Options


class OptionsExtractor():
    """Initialize options variables provided in the yaml file"""
    def parse_options(self, yaml_file):
        options = Options(yaml_file["Options"])

        return options
