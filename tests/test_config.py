import pytest


def test_config_gets_correct_values(config_file):
    """Test if the YAMLGetter class gets the values we expect it to get."""

    # The blackbox package needs to be imported after patching open()
    # because the get_yaml_config() is called implicitly at package import
    # that's why these imports are here
    from blackbox.config import Blackbox
    from blackbox.utils.yaml import get_yaml_config

    _config = get_yaml_config()

    for name, value in Blackbox:
        if name in _config:
            assert _config[name] == value


def test_config_render_fails(config_file_with_errors):
    """Test if the YAMLGetter class gets the values we expect it to get."""

    # The blackbox package needs to be imported after patching open()
    # because the get_yaml_config() is called implicitly at package import
    # that's why these imports are here
    from blackbox.exceptions import ImproperlyConfigured
    from blackbox.utils.yaml import get_yaml_config

    with pytest.raises(ImproperlyConfigured):
        get_yaml_config()


def test_config_missing_value(config_file_with_missing_value):
    """Test if the YAMLGetter class gets the values we expect it to get."""

    # The blackbox package needs to be imported after patching open()
    # because the get_yaml_config() is called implicitly at package import
    # that's why these imports are here

    from blackbox.exceptions import ImproperlyConfigured
    from blackbox.utils.yaml import get_yaml_config

    with pytest.raises(ImproperlyConfigured):
        get_yaml_config()
