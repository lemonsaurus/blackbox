import re

PARAMS_REGEX = r"(?:\?|&|;)([^=]+)=([^&|;]+)"


class ConnstringParserMixin:
    """A mixin class for handlers that depend on connstrings."""

    # How will the connstring be parsed? Subclasses must define this expression.
    connstring_regex = r""

    # What are the valid URI protocols for this connstring?
    valid_prefixes = []

    def __init__(self, *args, **kwargs):
        """Ensure that the connstrings are set up correctly."""
        self.connstring: str = kwargs.pop("connstring", "")

    @property
    def config(self) -> dict:
        """
        Parse the connstring and return its constituent parts.

        Uses the connstring_regex defined in the subclass, but also parses out any
        URL-style additional parameters and adds those to the dictionary.

        So, if you've got a connstring like `stuff://internet:dingdong?fire=ice&magic=blue`,
        and you're working with a connstring_regex like `stuff://(?P<user>.+):(?P<password>.+)`,
        self.config will look like this:
        {
            "user": "internet",
            "password": "dingdong",
            "fire": "ice",
            "magic": "blue,
        }
        """
        config = {}
        if self.enabled:
            config = re.search(self.connstring_regex, self.connstring).groupdict()

            # Now, let's parse out any params specified behind the connstring,
            # like fruit and dino in `s3://user:password?fruit=lemon&dino=saurus`
            for param, value in re.findall(PARAMS_REGEX, self.connstring):
                config[param] = value

        return config

    @property
    def enabled(self) -> bool:
        """
        A property that tells us whether the handler is enabled or not.

        This only has to be overridden if you need some sort of custom logic for it.
        """
        if self.connstring and self.connstring_regex:
            return True
        return False

    @classmethod
    @property
    def prefix_regex(cls) -> str:
        """
        Returns a regex string that groups the handler name to their valid prefixes.
        """
        name = cls.__name__
        prefixes = "|".join(cls.valid_prefixes)
        return f"(?P<{name}>{prefixes})"

    def __repr__(self):
        return f"{self.__class__}('{self.connstring}')"
