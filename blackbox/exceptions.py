import typing as t


class ImproperlyConfigured(Exception):
    """A class for raising configuration errors in our handlers."""


class MissingFields(ImproperlyConfigured):
    """Exception for missing configuration fields in handlers."""

    def __init__(self, handler: str, name: str, id_: t.Optional[str], fields: list[str]):
        id_info = f" with id {id_}" if id_ is not None else ""
        missing_fields = ", ".join(fields)

        self.message = f"Missing configuration key(s) for {handler} {name}{id_info}: {missing_fields}"
        super().__init__(self.message)
