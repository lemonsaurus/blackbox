import pytest

from blackbox.config import Blackbox
from blackbox.exceptions import ImproperlyConfigured
from blackbox.handlers.databases import Postgres
from blackbox.handlers.databases import Redis


def test_postgres_handler_can_be_instantiated_with_one_connstring(config_file):
    """Test if the PostgreSQL database handler can be instantiated."""
    Postgres()


def test_postgres_fails_with_multiple_connstrings(config_file):
    """Test if the PostgreSQL database handler can be instantiated with multiple connstrings."""

    Blackbox.databases.append("postgres:/blabla")

    with pytest.raises(ImproperlyConfigured):
        Postgres()


def test_redis_handler_can_be_instantiated(config_file):
    """Test if the Redis database handler can be instantiated."""

    Redis()
