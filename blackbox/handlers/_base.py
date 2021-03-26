from abc import ABC

from blackbox.exceptions import MissingFields


class BlackboxHandler(ABC):
    """An abstract base handler."""

    required_fields = ()
    handler_type = ""

    def __init__(self, **config):
        self.config = config
        self._validate_config()

    def _validate_config(self):
        """Ensure required configuration fields were passed to the handler."""
        handler_name = self.__class__.__name__
        missing_fields = [field for field in self.required_fields if field not in self.config]

        if missing_fields:
            raise MissingFields(self.handler_type, handler_name, self.config.get("id"), missing_fields)

    def teardown(self) -> None:
        """
        This gets called at the end of the handlers life.

        It doesn't need to be implemented, but it can be if you need to do some form of
        teardown or cleanup after your handler has done whatever it is designed to do.
        """
        return None
