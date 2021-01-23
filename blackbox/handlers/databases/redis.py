import datetime
import logging
from pathlib import Path

from blackbox.handlers.databases._base import BlackboxDatabase
from blackbox.utils import run_command
from blackbox.utils.logger import log


class Redis(BlackboxDatabase):
	"""A Database handler that will run a redis-cli command for Redis backup."""

	connstring_regex = r"redis://(?P<password>.+)@(?P<host>.+):(?P<port>.+)"
	valid_prefixes = [
	    "redis"
	]

	def backup(self) -> Path:
		"""Dump all the data to a file and then return the filepath."""
		date = datetime.date.today().strftime("%d_%m_%Y")
		backup_path = Path.home() / f"redis_blackbox_{date}.rdb"

		# Run the backup, and store the outcome.
		self.success, self.output = run_command(
			"redis-cli "
			f"-h {self.config.get('host')} "
			f"-p {self.config.get('port')} "
			f"--rdb {backup_path}",
			REDISCLI_AUTH=self.config.get("password")
		)
		log.debug(self.output)

		# Return the path to the backup file
		return backup_path
