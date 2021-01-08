import unittest

from blackbox.config import Blackbox
from blackbox.exceptions import ImproperlyConfigured
from blackbox.handlers import MongoDB, Postgres, Redis


class BlackBoxDatabaseTests(unittest.TestCase):

    def test_mongodb_handler_can_be_instantiated(self):
        """Test if the MongoDB database handler can be instantiated."""
        try:
            MongoDB()
        except ImproperlyConfigured:
            self.fail("Mongo() could not be instantiated.")

    def test_postgres_handler_can_be_instantiated_with_one_connstring(self):
        """Test if the PostgreSQL database handler can be instantiated."""
        try:
            Blackbox.databases = [
                "postgres://user:password@host:port",
            ]
            Postgres()
        except ImproperlyConfigured:
            self.fail("Postgres() could not be instantiated.")

    def test_postgres_fails_with_multiple_connstrings(self):
        """Test if the PostgreSQL database handler can be instantiated with multiple connstrings."""
        with self.assertRaises(ImproperlyConfigured):
            Blackbox.databases = [
                "postgres://johnwasafraid",
                "postgres://lellowmelon"
            ]
            Postgres()

    def test_redis_handler_can_be_instantiated(self):
        """Test if the Redis database handler can be instantiated."""
        try:
            Redis()
        except ImproperlyConfigured:
            self.fail("Redis() could not be instantiated.")
