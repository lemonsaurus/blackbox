import requests

from blackbox.handlers.notifiers._base import BlackboxNotifier


class Json(BlackboxNotifier):
    """A notifier for sending webhooks to a backend."""

    required_fields = ("url",)

    def _parse_report(self) -> dict:
        """Turn the report into something the notify function can use."""
        payload = []

        # Iterate over each database report we have
        # For each report, we will include
        # 1. Which database are we backing up ?
        # 2. Was the backup successful overall ?
        # 3. Any output that we might have gotten back during the backup
        for database in self.report.databases:
            database_payload = {
                "source": database.database_id,
                "success": database.success,
                "output": database.output or None
            }

            storages_payload = []
            # A single database can be backed up in multiple storage points
            # For each database, we include the storage provider and
            # whether the backup succeeded or not
            # for that particular storage point.
            for provider in database.storages:
                storages_payload.append({"name": provider.storage_id, "success": provider.success})

            # Aggregate the storage points data with the current database
            database_payload['backup'] = storages_payload
            payload.append(database_payload)

        return {"backup-data": payload}

    def notify(self):
        """Send a webhook to a particular url with a blackbox report."""
        requests.post(self.config["url"], json=self._parse_report())
