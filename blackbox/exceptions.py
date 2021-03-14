import typing as t


class ImproperlyConfigured(Exception):
    """A class for raising configuration errors in our handlers."""


class MissingFields(ImproperlyConfigured):
    """Exception for missing configuration fields in handlers."""

    def __init__(self, handler: str, name: str, id_: t.Optional[str], fields: list[str]):
        id_info = f" with id {id_}" if id_ is not None else ""
        field_info = ', '.join(fields)
        self.message = f"Missing configuration key(s) for {handler} {name}{id_info}: {field_info}"
        super().__init__(self.message)


class InvalidHandler(ImproperlyConfigured):
    """
    Exception for configured handlers that do not exist.

    Example: Defining a database "Postman" or a storage "Droopbox"
    """

    def __init__(self, handler: str):
        self.message = f"Invalid handler: {handler}"
        super().__init__(self.message)


class UnknownId(ImproperlyConfigured):
    """
    Exception for configured ids that do not exist.

    Example: Specifying a storage with id `main_bucket` when that id does not exist
             in the `storages` section
    """

    def __init__(self, database: str, database_id: str, id_: str):
        self.message = (
            f"Unknown id specified for database {database} with id {database_id}: {id_}"
        )
        super().__init__(self.message)
