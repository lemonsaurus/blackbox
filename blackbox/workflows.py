from collections import defaultdict
import dataclasses
import re
from typing import TypeVar

from blackbox.config import Blackbox as CONFIG
from blackbox.exceptions import ImproperlyConfigured
from blackbox.handlers._base import BlackboxHandler
from blackbox.handlers.databases import BlackboxDatabase
from blackbox.handlers.storage import BlackboxStorage
from blackbox.handlers.notifiers import BlackboxNotifier

Handler = TypeVar("Handler", bound=BlackboxHandler)


@dataclasses.dataclass
class Workflow:
    """Dataclass that stores databases and the storage and notifiers specified for each."""
    database: BlackboxDatabase
    storage_providers: set[BlackboxStorage] = dataclasses.field(default_factory=set)
    notifiers: set[BlackboxNotifier] = dataclasses.field(default_factory=set)


def get_configured_handlers(HandlerType: type[Handler], connstrings: list[str]) -> dict[str, set[Handler]]:
    """Configures and instantiates handlers based on the given connstrings."""
    # Mapping of handler name to handler
    # handler_dict = {"Postgres": Postgres, "MongoDB": MongoDB}
    handler_dict = {
        Handler.__name__: Handler
        for Handler in HandlerType.__subclasses__()
    }
    # Regex for all valid handler prefixes
    # PREFIX_REGEX = "(?P<Postgres>postgres|postgresql)|(?P<MongoDB>mongodb)"
    PREFIX_REGEX = "|".join(Handler.prefix_regex for Handler in HandlerType.__subclasses__())

    configured_handlers = defaultdict(set)
    for connstring in connstrings:
        # Check if connstring matches a valid prefix
        if match := re.match(PREFIX_REGEX, connstring):
            # Retrieve the handler from the matched group name
            Handler = handler_dict[match.lastgroup]
            handler = Handler(connstring=connstring)

            # Add to general id
            configured_handlers["all"].add(handler)

            # Add to specified ids if exists
            if id := handler.config.get("id", "").lower():
                for i in id.split(","):
                    configured_handlers[i].add(handler)

            # Add to handler type id
            configured_handlers[Handler.__name__.lower()].add(handler)
        else:
            raise ImproperlyConfigured(f"Unknown {HandlerType.__name__}: {connstring}")

    return configured_handlers


def get_handlers_by_id(id_: str, handlers: dict[str, set[Handler]]) -> set[Handler]:
    """
    Given an id and a mapping of id to handlers, return handlers matching the ids.

    `id_` may be a comma separated list of ids as a string.
    Raises ImproperlyConfigured if the id is not found.
    """
    match = set()
    for wanted_handler in id_.rstrip(",").split(","):
        try:
            match.update(handlers[wanted_handler])
        except KeyError:
            raise ImproperlyConfigured(f"Unknown id: {wanted_handler}")
    return match


def get_workflows() -> list[Workflow]:
    """Returns a list of Workflow objects based on the configuration."""
    providers = get_configured_handlers(BlackboxStorage, CONFIG.storage)
    notifiers = get_configured_handlers(BlackboxNotifier, CONFIG.notifiers)
    databases = get_configured_handlers(BlackboxDatabase, CONFIG.databases)

    workflows = []
    for database in databases["all"]:
        workflow = Workflow(database)

        # Update storage providers
        if provider_id := database.config.get("storage_providers"):
            wanted_providers = get_handlers_by_id(provider_id, providers)
            workflow.storage_providers.update(wanted_providers)
        else:
            workflow.storage_providers.update(providers["all"])

        # Update notifiers
        if notifier_id := database.config.get("notifiers"):
            wanted_notifiers = get_handlers_by_id(notifier_id, notifiers)
            workflow.notifiers.update(wanted_notifiers)
        else:
            workflow.notifiers.update(notifiers["all"])

        workflows.append(workflow)
    return workflows
