import pathlib

import yaml


def get_yaml_config() -> dict:
    """Load the yaml file in the root folder, and return it as a dict."""
    root_folder = pathlib.Path(__file__).parent.parent.absolute()
    with open(root_folder / "config.yaml", encoding="UTF-8") as f:
        return yaml.safe_load(f)
