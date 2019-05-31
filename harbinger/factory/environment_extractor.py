"""
EnvironmentExtractor class:
    - extracts environment options from the yaml file and passes
    them into the Environment class to be initialized
"""

from harbinger.factory.environment import Environment


class EnvironmentExtractor():
    """Initialize environment variables provided in the yaml file"""

    def parse_environment(self, yaml_file):
        environment = Environment(yaml_file["Environment"])

        return environment
