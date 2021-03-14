import dataclasses
import typing as t
from collections import defaultdict
from itertools import chain

from blackbox import exceptions
from blackbox.config import Blackbox as CONFIG
from blackbox.handlers import BlackboxDatabase
from blackbox.handlers import BlackboxNotifier
from blackbox.handlers import BlackboxStorage
from blackbox.handlers._base import BlackboxHandler


Handler = t.TypeVar("Handler", bound=BlackboxHandler)
HandlerById = t.Mapping[str, set[Handler]]


@dataclasses.dataclass
class Workflow:
    """Dataclass that stores a database and the storage and notifiers specified for each."""

    database: BlackboxDatabase
    storage_providers: set[BlackboxStorage] = dataclasses.field(default_factory=set)
    notifiers: set[BlackboxNotifier] = dataclasses.field(default_factory=set)


# Get a mapping of handler names to their class objects ("postgres" to Postgres)
# Example:
#   HANDLER_MAPPING = { "postgres": Postgres, "discord": Discord }
components = (BlackboxDatabase, BlackboxNotifier, BlackboxStorage)

HANDLER_MAPPING: dict[str, t.Type[BlackboxHandler]] = {
    handler.__name__.lower(): handler
    for handler in chain.from_iterable(component.__subclasses__() for component in components)
}


def get_configured_handlers(config: dict) -> dict:
    """
    Instantiate handlers based on the given configuration.

    Returns a dictionary mapping handler ids to handler instances.
    Adds additional ids "all" and <handler_type> (eg. postgres, s3).
    """
    handler_dict = defaultdict(set)

    # Get handlers
    for handler_type, handler_config in config.items():
        try:
            Handler = HANDLER_MAPPING[handler_type]
        except KeyError:
            raise exceptions.InvalidHandler(handler_type)

        for handler_id, handler_fields in handler_config.items():
            handler_instance = Handler(**handler_fields, id=handler_id)

            # Set of all handlers
            handler_dict["all"].add(handler_instance)
            # Set of all handler type, ie. postgres/s3/discord
            handler_dict[handler_type].add(handler_instance)
            # Set of handlers with the specified id
            handler_dict[handler_id].add(handler_instance)

    return handler_dict


def get_handlers_by_id(id_: t.Union[str, list[str]], handlers: HandlerById[Handler]) -> set[Handler]:
    """
    Given ids and a mapping of id to handlers, return handlers matching the ids.

    `id_` can be a string or a list of strings corresponding to ids.
    Raises TypeError if id_ is not a string or a list.
    Raises KeyError if id_ does not correspond to a handler in `handlers`.
    """
    if not isinstance(id_, (str, list)):
        raise TypeError

    # Turn string into a list with one string for simple iteration
    ids = [id_] if isinstance(id_, str) else id_

    match = set()
    for i in ids:
        match.update(handlers[i])
    return match


def get_workflows() -> list[Workflow]:
    """Return a list of workflows based on configured handlers."""
    workflows = []

    if not CONFIG.databases or not CONFIG.storage:
        raise exceptions.ImproperlyConfigured("You have to define least one database and storage")

    database_handlers = get_configured_handlers(CONFIG.databases)["all"]
    storage_handlers = get_configured_handlers(CONFIG.storage)
    notifier_handlers = get_configured_handlers(CONFIG.notifiers)

    for database in database_handlers:
        workflow = Workflow(database)

        try:
            # Assign storage providers
            wanted_providers = database.config.get("storage_providers", "all")
            storage_providers = get_handlers_by_id(wanted_providers, storage_handlers)
            workflow.storage_providers.update(storage_providers)

            # Assign notifiers
            wanted_notifiers = database.config.get("notifiers", "all")
            notifiers = get_handlers_by_id(wanted_notifiers, notifier_handlers)
            workflow.notifiers.update(notifiers)
        except TypeError:
            raise exceptions.ImproperlyConfigured(
                "storage_providers and notifiers have to be a list of ids or an id"
            )
        except KeyError as e:
            raise exceptions.UnknownId(
                database.__class__.__name__, database.config["id"], e.args[0]
            )

        workflows.append(workflow)
    return workflows
