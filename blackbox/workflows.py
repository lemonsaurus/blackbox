import dataclasses
import re
import typing as t
from collections import defaultdict

from blackbox.exceptions import ImproperlyConfigured
from blackbox.handlers._base import BlackboxHandler
from blackbox.handlers.databases import BlackboxDatabase
from blackbox.handlers.notifiers import BlackboxNotifier
from blackbox.handlers.storage import BlackboxStorage
from blackbox.utils.logger import log


Handler = t.TypeVar("Handler", bound=BlackboxHandler)
HandlerById = t.Mapping[str, set[Handler]]


@dataclasses.dataclass
class Workflow:
    """Dataclass that stores a database and the storage and notifiers specified for each."""

    database: BlackboxDatabase
    storage_providers: set[BlackboxStorage] = dataclasses.field(default_factory=set)
    notifiers: set[BlackboxNotifier] = dataclasses.field(default_factory=set)


def get_configured_handlers(
    HandlerType: type[Handler], connstrings: list[str]
) -> HandlerById[Handler]:
    """Configures and instantiates handlers based on the given connstrings."""
    # Mapping of handler name to handler instance
    # handler_dict = {"Postgres": Postgres, "MongoDB": MongoDB}
    handler_dict = {
        handler.__name__: handler for handler in HandlerType.__subclasses__()
    }
    log.debug(f"Available handlers: {handler_dict}")

    # Regex for all valid handler prefixes
    # PREFIX_REGEX = "(?P<Postgres>postgres|postgresql)|(?P<MongoDB>mongodb)"
    PREFIX_REGEX = "|".join(
        # We know the property returns a string, but the typechecker doesn't
        t.cast(str, handler.prefix_regex) for handler in HandlerType.__subclasses__()
    )

    configured_handlers = defaultdict(set)
    for connstring in connstrings:
        log.debug(f"Parsing connstring: {connstring}")
        # Check if connstring matches a valid prefix
        if match := re.match(PREFIX_REGEX, connstring):
            # PREFIX_REGEX is always built with a group name, so match.lastgroup is never None
            matched_group = t.cast(str, match.lastgroup)

            log.debug(f"Connstring matches: {matched_group}")
            # Retrieve the handler from the matched group name
            handler_class = handler_dict[matched_group]
            handler = handler_class(connstring=connstring)

            # Add to general id
            configured_handlers["all"].add(handler)

            # Add to specified ids if exists
            if id_ := handler.config.get("id", "").lower():
                for i in id_.split(","):
                    configured_handlers[i].add(handler)

            # Add to handler type id
            configured_handlers[handler_class.__name__.lower()].add(handler)
        else:
            raise ImproperlyConfigured(f"Unknown {HandlerType.__name__}: {connstring}")

    return configured_handlers


def get_handlers_by_id(id_: str, handlers: HandlerById[Handler]) -> set[Handler]:
    """
    Given an id and a mapping of id to handlers, return handlers matching the ids.

    `id_` may be a comma separated list of ids as a string.
    Raises ImproperlyConfigured if the id is not found.
    """
    match = set()
    for wanted_handler in id_.rstrip(",").split(","):
        try:
            wanted_handlers = handlers[wanted_handler]
            match.update(wanted_handlers)
        except KeyError:
            raise ImproperlyConfigured(f"Unknown id: {wanted_handler}")
    return match


def get_workflows(
    databases: HandlerById[BlackboxDatabase],
    storage_providers: HandlerById[BlackboxStorage],
    notifiers: HandlerById[BlackboxNotifier],
) -> list[Workflow]:
    """Returns a list of Workflow objects based on the handlers passed."""
    workflows = []
    for database in databases["all"]:
        workflow = Workflow(database)

        # Update storage providers
        if provider_id := database.config.get("storage_providers"):
            wanted_providers = get_handlers_by_id(provider_id, storage_providers)
            workflow.storage_providers.update(wanted_providers)
        else:
            workflow.storage_providers.update(storage_providers["all"])

        # Update notifiers
        if notifier_id := database.config.get("notifiers"):
            wanted_notifiers = get_handlers_by_id(notifier_id, notifiers)
            workflow.notifiers.update(wanted_notifiers)
        else:
            workflow.notifiers.update(notifiers["all"])

        workflows.append(workflow)
    return workflows
