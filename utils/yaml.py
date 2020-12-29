import pathlib

import yaml

from config.exceptions import ImproperlyConfigured


def get_yaml_config() -> dict:
    """Load the yaml file in the root folder, and return it as a dict."""
    root_folder = pathlib.Path(__file__).parent.parent.absolute()

    try:
        with open(root_folder / "config.yaml", encoding="UTF-8", mode="r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError as e:
        raise ImproperlyConfigured(
            "You must create a config.yaml file in the root folder! "
            "See the readme under 'Configuration' for more information."
        ) from e