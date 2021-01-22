from blackbox.utils.yaml import get_yaml_config
from blackbox.utils.logger import log

_CONFIG_YAML = get_yaml_config()


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

    def _get_annotation(cls, name):
        """Fetch the annotation configured in the subclass."""
        return cls.__annotations__.get(name)

    def __getattr__(cls, name):
        """
        Fetch the attribute in the _CONFIG_YAML dictionary.

        This just attempts to do a dictionary lookup in the _CONFIG_YAML we unpacked earlier,
        and supports sections and subsections if we need nested blackbox data.
        """
        name = name.lower()

        try:
            if cls.section is None:
                return _CONFIG_YAML[name]
            elif cls.subsection is None:
                return _CONFIG_YAML[cls.section][name]
            else:
                return _CONFIG_YAML[cls.section][cls.subsection][name]
        except KeyError as e:
            # If one of the handler lists isn't defined, return an empty list.
            log.warning(f"{name} is not defined in the config.yaml file -- returning an falsy value.")
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
