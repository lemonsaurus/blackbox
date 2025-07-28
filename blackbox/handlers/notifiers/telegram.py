import telebot
from telebot.apihelper import ApiTelegramException

from blackbox.handlers.notifiers._base import BlackboxNotifier
from blackbox.utils.logger import log


CHECKMARK_EMOJI = "\U00002705"  # ✔
FAIL_EMOJI = "\U0000274C"       # ❌
WARNING_EMOJI = "\U000026A0"    # ⚠


class Telegram(BlackboxNotifier):
    """Telegram notifier for Blackbox."""

    required_fields = ("token", "chat_id",)
    # Telegram bot API message character limit is 4096 UTF-8 characters
    max_output_chars = 4096

    def _parse_report(self) -> str:
        """Convert the report object to a Telegram-friendly string."""
        data_report = "Blackbox Backup Status:\n"

        for db in self.report.databases:
            data_report += f"{db.database_id}: \n"
            for storage in db.storages:
                if storage.success:
                    data_report += f"{CHECKMARK_EMOJI} {storage.storage_id}\n"
                else:
                    data_report += f"{FAIL_EMOJI} {storage.storage_id}\n"
        # Add optimized output for failed databases
        if not self.report.success:
            optimized_output = self.get_optimized_output()
            if optimized_output:
                data_report += f"\n{WARNING_EMOJI} Output:\n{optimized_output}\n"
        return data_report

    def notify(self):
        """Convert report dict to string and send via Telegram."""
        bot = telebot.TeleBot(self.config["token"])
        try:
            bot.send_message(
                chat_id=self.config["chat_id"],
                text=self._parse_report(),
            )
        except ApiTelegramException:
            log.debug(
                "Telegram API key or user_id is wrong "
                "or you forgot to press /start in your bot."
            )
