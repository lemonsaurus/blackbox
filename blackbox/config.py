import os
from pathlib import Path

from blackbox.utils.logger import log
from blackbox.utils.yaml import get_yaml_config


class YAMLGetter(type):
    """
    Metaclass for accessing yaml blackbox data.

    Supports getting configuration from up to two levels
    of nested configuration through `section` and `subsection`.
    - `section` specifies the YAML configuration section (or "key") in which the configuration lives.
    - `subsection` specifies the section within the section from which configuration should be loaded.

    If neither are these are set, it'll just try to get it from the root level.

    Adapted from python-discord/bot.

    Example Usage:
        # blackbox.yml
        bot:
            prefixes:
                direct_message: ''
                guild: '!'

        # blackbox.py
        class Prefixes(metaclass=YAMLGetter):
            section = "bot"
            subsection = "prefixes"

        # Usage in Python code
        from blackbox import Prefixes

        print(Prefixes.direct_message)
        print(Prefixes.guild)
    """
    section = None
    subsection = None
    _config = None

    @classmethod
    def parse_config(cls, config_path: Path = None):
        """Parse the config from the blackbox.yaml file."""

        # If config_path is passed, use that.
        env_config_path = os.environ.get("BLACKBOX_CONFIG_PATH")

        # If there is a path to the config, parse it
        if config_path:
            cls._config = get_yaml_config(config_path)

        # Otherwise, if there's an environment variable with a path, we'll use that.
        elif env_config_path:
            cls._config = get_yaml_config(Path(env_config_path))

        # Otherwise, we expect the config file to be in the root folder,
        # and to be called 'blackbox.yaml'
        else:
            root_folder = Path(__file__).parent.parent.absolute()
            cls._config = get_yaml_config(root_folder / "blackbox.yaml")

    def _get_annotation(cls, name):
        """Fetch the annotation configured in the subclass."""
        return cls.__annotations__.get(name)

    def __getattr__(cls, name):
        """
        Fetch the attribute in the `YAMLGetter.config` dictionary.

        This just attempts to do a dictionary lookup in `YAMLGetter.config`,
        and supports sections and subsections if we need nested blackbox data.
        """
        name = name.lower()

        # Here's a bit of magic - We don't set the cls._config until the first time
        # something tries to actually call this method. This kind of just-in-time approach
        # allows us to comfortably modify the `_config` at some point before we start using
        # any of the Handlers, without worrying about any race conditions.
        #
        # If you need this config to be set before or after the first call to __getattr__, simply call
        # YAMLGetter.parse_config(). You can pass in a configuration file path if you need to.
        if not cls._config:
            cls.parse_config()

        try:
            if cls.section is None:
                return cls._config[name]
            elif cls.subsection is None:
                return cls._config[cls.section][name]
            else:
                return cls._config[cls.section][cls.subsection][name]
        except KeyError:
            # If one of the handler lists isn't defined, return an empty list.
            log.warning(f"{name} is not defined in the blackbox.yaml file -- returning an falsy value.")
            if cls._get_annotation(name) == list:
                return []
            elif cls._get_annotation(name) == dict:
                return {}
            else:
                return None

    def __getitem__(cls, name):
        """Just defer to the __getattr__ implementation."""
        return cls.__getattr__(name)

    def __iter__(cls):
        """Return generator of key: value pairs of current constants class' blackbox values."""
        for name in cls.__annotations__:
            yield name, getattr(cls, name)


class Blackbox(metaclass=YAMLGetter):
    """The configuration for the blackbox application."""
    # Handlers
    databases: list
    storage: list
    notifiers: list

    # Configuration
    retention_days: int
