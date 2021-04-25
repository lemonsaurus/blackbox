import telebot
from telebot.apihelper import ApiTelegramException

from blackbox.handlers.notifiers._base import BlackboxNotifier
from blackbox.utils.logger import log


STRING_LIMIT = 2000  # Limit output
CHECKMARK_EMOJI = "\U00002705"  # ✔
FAIL_EMOJI = "\U0000274C"       # ❌
WARNING_EMOJI = "\U000026A0"    # ⚠


class Telegram(BlackboxNotifier):
    """Telegram notifier for Blackbox."""

    required_fields = ("token", "chat_id",)

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
            if db.success is False:
                data_report += f"{WARNING_EMOJI} {db.output[:STRING_LIMIT]}\n"
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
