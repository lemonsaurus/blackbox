import os
import pathlib

import yaml
from jinja2 import Environment
from jinja2 import StrictUndefined
from jinja2.exceptions import TemplateSyntaxError
from jinja2.exceptions import UndefinedError

from blackbox.exceptions import ImproperlyConfigured


def get_yaml_config(config_path: pathlib.Path) -> dict:
    """Load the yaml file in the root folder, and return it as a dict."""
    template = Environment(undefined=StrictUndefined)

    try:
        with open(config_path, encoding="UTF-8", mode="r") as f:
            # Inject the local environment variables into the rendering context.
            # This bit of magic allows us to resolve any {{ VARIABLE }} to whatever
            # the value of the equivalent environment variable is.
            parsed_config = template.from_string(f.read()).render(**os.environ)
            return yaml.safe_load(parsed_config)

    except TemplateSyntaxError as e:
        raise ImproperlyConfigured(
            f"There is an error in the config file: {e}"
        ) from e

    except UndefinedError as e:
        raise ImproperlyConfigured(
            f"Missing environment variable: {e}"
        ) from e

    except FileNotFoundError as e:
        raise ImproperlyConfigured(
            f"Your blackbox.yaml file was not found at {config_path}!\n"
            "See the readme under 'Configuration' for more information."
        ) from e
