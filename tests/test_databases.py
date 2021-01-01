import unittest

from config.exceptions import ImproperlyConfigured
from databases import MongoDB, Postgres, Redis


class BlackBoxDatabaseTests(unittest.TestCase):

    def test_mongodb_handler_can_be_instantiated(self):
        """Test if the MongoDB database handler can be instantiated."""
        try:
            MongoDB()
        except ImproperlyConfigured:
            self.fail("Mongo() could not be instantiated.")

    def test_postgres_handler_can_be_instantiated(self):
        """Test if the PostgreSQL database handler can be instantiated."""
        try:
            Postgres()
        except ImproperlyConfigured:
            self.fail("Postgres() could not be instantiated.")

    def test_redis_handler_can_be_instantiated(self):
        """Test if the Redis database handler can be instantiated."""
        try:
            Redis()
        except ImproperlyConfigured:
            self.fail("Redis() could not be instantiated.")
