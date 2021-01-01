from abc import ABC, abstractmethod


class BlackboxConnstringParser(ABC):
    """An abstract class for handlers that depend on connstrings."""

    @abstractmethod
    def _get_connstring(self):
        """Try to get the connstring out of the config."""
        raise NotImplementedError

    @abstractmethod
    def _parse_connstring(self):
        """Parse the connstring and return its constituent parts."""
        raise NotImplementedError

    @property
    def enabled(self):
        """
        A property that tells us whether the handler is enabled or not.

        This only has to be overridden if you need some sort of custom logic for it.
        """
        if self._get_connstring():
            return True
        return False
