import unittest

from blackbox.config import Blackbox
from blackbox.utils.yaml import get_yaml_config


class BlackBoxConfigTests(unittest.TestCase):

    def test_config_gets_correct_values(self):
        """Test if the YAMLGetter class gets the values we expect it to get."""
        _config = get_yaml_config()

        for name, value in Blackbox:
            if name in _config:
                self.assertEqual(_config[name], value)
