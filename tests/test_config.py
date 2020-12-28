import unittest

from config import BlackBox
from utils.yaml import get_yaml_config


class BlackBoxConfigTests(unittest.TestCase):

    def test_config_gets_correct_values(self):
        """Test if the YAMLGetter class gets the values we expect it to get."""
        _config = get_yaml_config()

        for name, value in BlackBox:
            self.assertEqual(_config[name], value)
