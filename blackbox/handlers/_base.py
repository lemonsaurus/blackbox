from abc import ABC

from blackbox.mixins import ConnstringParserMixin


class BlackboxHandler(ABC, ConnstringParserMixin):
    """An abstract base handler."""

    def teardown(self) -> None:
        """
        This gets called at the end of the handlers life.

        It doesn't need to be implemented, but it can be if you need to do some form of
        teardown or cleanup after your handler has done whatever it is designed to do.
        """
        return None
