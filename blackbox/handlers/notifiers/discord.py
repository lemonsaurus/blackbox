import requests

from blackbox.handlers.notifiers._base import BlackboxNotifier


class Discord(BlackboxNotifier):
    """A notifier for sending webhooks to Discord."""

    required_fields = ("webhook",)

    def _get_optimized_output(self) -> str:
        """
        Generate optimally truncated output for failed databases only.

        Only includes output from databases that failed, using tail of logs
        and optimal character allocation to maximize relevant information.
        """
        # Get failed databases only
        failed_databases = [db for db in self.report.databases if not db.success]

        if not failed_databases:
            return ""

        # Get tail of each failed database output (last 10 lines max)
        database_outputs = []
        for db in failed_databases:
            lines = db.output.strip().split('\n')
            tail_lines = lines[-10:] if len(lines) > 10 else lines
            tail_output = '\n'.join(tail_lines)
            database_outputs.append((db.database_id, tail_output))

        # If only one failed database, just truncate to last 1024 chars
        if len(database_outputs) == 1:
            db_id, output = database_outputs[0]
            if len(output) <= 1024:
                return output
            return output[-1024:]  # Take last 1024 characters

        # Multiple failed databases - use optimal allocation algorithm
        return self._allocate_characters_optimally(database_outputs)

    def _allocate_characters_optimally(self, database_outputs: list[tuple[str, str]]) -> str:
        """
        Implement optimal character allocation algorithm from issue #155.

        Sorts outputs by length and allocates characters to minimize truncation
        while staying within Discord's 1024 character limit.
        """
        # Sort by output length (smallest first)
        sorted_outputs = sorted(database_outputs, key=lambda x: len(x[1]))

        total_budget = 1024
        allocated_outputs = []
        remaining_services = len(sorted_outputs)

        for db_id, output in sorted_outputs:
            # Calculate budget for this service
            budget_per_service = total_budget // remaining_services

            # Calculate the formatted output length including separators
            separator_overhead = len("\n\n") if allocated_outputs else 0
            db_prefix = f"{db_id}: "

            if len(output) + len(db_prefix) + separator_overhead <= budget_per_service:
                # Output fits within budget, use as-is
                formatted = f"{db_id}: {output}"
                allocated_outputs.append(formatted)
                total_budget -= (len(formatted) + separator_overhead)
            else:
                # Output exceeds budget, truncate from start (keep tail)
                available_chars = budget_per_service - len(db_prefix) - separator_overhead
                if available_chars > 0:
                    truncated = output[-available_chars:]
                    formatted = f"{db_id}: {truncated}"
                    allocated_outputs.append(formatted)
                    total_budget -= budget_per_service
                else:
                    # Not enough space even for the database ID
                    break

            remaining_services -= 1

        return "\n\n".join(allocated_outputs)

    def _parse_report(self) -> dict:
        """Turn the report into something the notify function can use."""
        # Generate optimally truncated output for failed databases only
        output = self._get_optimized_output()

        # Was this a success?
        success = self.report.success
        color = 1024049 if success else 13377568

        # Make a list of database fields
        fields = []
        for database in self.report.databases:
            field = {
                "name": f"**{database.database_id}**",
                "inline": True,
                "value": ""
            }

            for provider in database.storages:
                emoji = ":white_check_mark:" if provider.success else ":x:"
                field['value'] += f"{emoji}  {provider.storage_id}\n"

            # If all backup fails, no storage statuses will be added to
            # database['storage']. Discord doesn't allow empty field
            # values, so we have to add the :x: emoji to the field to
            # prevent the webhook endpoint from raising an error.
            if not field['value']:
                field['value'] = ":x:"

            # Strip any trailing newlines and append
            field['value'] = field['value'].strip()
            fields.append(field)

        # Add the output, but only if the overall report is a failure.
        if not success:
            fields.append({
                "name": "Output",
                "value": output,
            })

        # Return the payload
        return {
            "content": None,
            "embeds": [
                {
                    "title": "Backup",
                    "color": color,
                    "fields": fields
                }
            ],
            "username": "blackbox",
            "avatar_url": "https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png"  # NOQA: E501
        }

    def notify(self):
        """Send a webhook to Discord with a blackbox report."""
        requests.post(self.config["webhook"], json=self._parse_report())
