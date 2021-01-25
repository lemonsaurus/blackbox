import pytest

from blackbox.config import Blackbox
from blackbox.config import YAMLGetter
from blackbox.exceptions import ImproperlyConfigured


def test_config_gets_correct_values(config_file):
    """Test if the YAMLGetter class gets the values we expect it to get."""
    YAMLGetter.parse_config()
    _config = YAMLGetter._config

    for name, value in Blackbox:
        if name in _config:
            assert _config[name] == value


def test_config_render_fails(config_file_with_errors):
    """Test if the YAMLGetter class gets the values we expect it to get."""
    with pytest.raises(ImproperlyConfigured):
        YAMLGetter.parse_config()


def test_config_missing_value(config_file_with_missing_value):
    """Test if the YAMLGetter class gets the values we expect it to get."""
    with pytest.raises(ImproperlyConfigured):
        YAMLGetter.parse_config()
