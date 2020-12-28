import unittest

from databases import MongoDB, Postgres, Redis


class BlackBoxDatabaseTests(unittest.TestCase):

    @staticmethod
    def test_mongodb_handler_can_be_instantiated():
        """Test if the MongoDB database handler can be instantiated."""
        MongoDB()

    @staticmethod
    def test_postgres_handler_can_be_instantiated():
        """Test if the PostgreSQL database handler can be instantiated."""
        Postgres()

    @staticmethod
    def test_redis_handler_can_be_instantiated():
        """Test if the Redis database handler can be instantiated."""
        Redis()
