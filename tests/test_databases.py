import pytest

from tests.fixtures import config_file


def test_mongodb_handler_can_be_instantiated(config_file):
    """Test if the MongoDB database handler can be instantiated."""

    from blackbox.handlers import MongoDB

    MongoDB()


def test_postgres_handler_can_be_instantiated_with_one_connstring(config_file):
    """Test if the PostgreSQL database handler can be instantiated."""

    from blackbox.handlers import Postgres

    Postgres()


def test_postgres_fails_with_multiple_connstrings(config_file):
    """Test if the PostgreSQL database handler can be instantiated with multiple connstrings."""

    from blackbox.config import Blackbox
    from blackbox.exceptions import ImproperlyConfigured
    from blackbox.handlers import Postgres

    with pytest.raises(ImproperlyConfigured):
        Blackbox.databases = [
            "postgres://johnwasafraid",
            "postgres://lellowmelon"
        ]
        Postgres()

# Not yet implemented
# def test_redis_handler_can_be_instantiated(config_file):
#     """Test if the Redis database handler can be instantiated."""

#     from blackbox.handlers import Redis

#     Redis()

