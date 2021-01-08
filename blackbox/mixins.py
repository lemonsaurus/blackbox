import re
from itertools import chain
from typing import Optional

from blackbox.config import Blackbox
from blackbox.exceptions import ImproperlyConfigured


class ConnstringParserMixin:
    """A mixin class for handlers that depend on connstrings."""

    # How will the connstring be parsed? Subclasses must define this expression.
    connstring_regex = r""

    # What are the valid URI protocols for this connstring?
    valid_uri_protocols = []

    def __init__(self):
        """Ensure that the connstrings are set up correctly."""
        self.connstring = self._get_connstring()

    @staticmethod
    def _get_all_connstrings() -> list:
        """Get all connstrings in the config."""
        return list(chain(
            Blackbox.databases,
            Blackbox.loggers,
            Blackbox.notifiers,
            Blackbox.storage
        ))

    def _get_connstring(self) -> Optional[str]:
        """Ensure we only have a single connstring configured, and return it."""
        connstrings = [
            connstring for connstring in self._get_all_connstrings()
            if connstring.split(":")[0] in self.valid_uri_protocols
        ]

        # No connstrings configured
        if len(connstrings) == 0:
            return ""

        # More than one connstring configured! Fail hard.
        elif len(connstrings) > 1:
            raise ImproperlyConfigured(
                "You cannot configure more than one connstring of the same type at a time!"
            )

        # If only a single connstring is configured, return it!
        return connstrings[0]

    @property
    def config(self) -> dict:
        """Parse the connstring and return its constituent parts."""
        if self.enabled:
            return re.search(self.connstring_regex, self.connstring).groupdict()

    @property
    def enabled(self) -> bool:
        """
        A property that tells us whether the handler is enabled or not.

        This only has to be overridden if you need some sort of custom logic for it.
        """
        if self.connstring and self.connstring_regex:
            return True
        return False
