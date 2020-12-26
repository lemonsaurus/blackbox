import logging
import pathlib

import yaml

log = logging.getLogger(__name__)

# Load the yaml file in the root folder
root_folder = pathlib.Path(__file__).parent.parent.absolute()
with open(root_folder / "config.yaml", encoding="UTF-8") as f:
    _CONFIG_YAML = yaml.safe_load(f)


class YAMLGetter(type):
    """
    Metaclass for accessing yaml config data.

    Supports getting configuration from up to two levels
    of nested configuration through `section` and `subsection`.
    - `section` specifies the YAML configuration section (or "key") in which the configuration lives.
    - `subsection` specifies the section within the section from which configuration should be loaded.

    If neither are these are set, it'll just try to get it from the root level.

    Adapted from python-discord/bot.

    Example Usage:
        # config.yml
        bot:
            prefixes:
                direct_message: ''
                guild: '!'

        # config.py
        class Prefixes(metaclass=YAMLGetter):
            section = "bot"
            subsection = "prefixes"

        # Usage in Python code
        from config import Prefixes

        print(Prefixes.direct_message)
        print(Prefixes.guild)
    """
    section = None
    subsection = None

    def __getattr__(cls, name):
        name = name.lower()

        try:
            if cls.section is None:
                return _CONFIG_YAML[name]
            elif cls.subsection is None:
                return _CONFIG_YAML[cls.section][name]
            else:
                return _CONFIG_YAML[cls.section][cls.subsection][name]
        except KeyError:
            dotted_path = '.'.join(
                (cls.section or "", cls.subsection or "", name)
            )
            log.critical(f"Tried accessing configuration variable at `{dotted_path}`, but it could not be found.")
            raise

    def __getitem__(cls, name):
        return cls.__getattr__(name)

    def __iter__(cls):
        """Return generator of key: value pairs of current constants class' config values."""
        for name in cls.__annotations__:
            yield name, getattr(cls, name)


class Config(metaclass=YAMLGetter):
    """The configuration for the black-box application."""
    # Databases
    redis_enabled: bool
    mongodb_enabled: bool
    postgres_enabled: bool

    # Storage providers
    gdrive_enabled: bool

    # Database rotation
    rotation_days: int
