import telebot
from telebot.apihelper import ApiTelegramException

from blackbox.handlers.notifiers._base import BlackboxNotifier
from blackbox.utils.logger import log


STRING_LIMIT = 2000  # Limit output


class Telegram(BlackboxNotifier):
    """ Telegram notifier for Blackbox """
    required_fields = ("token", "chat_id",)

    def _parse_report(self) -> str:
        """ Telegram needs a string. Parsing report """
        data_report = "Blackbox Backup Status:\n"

        for db in self.report.databases:
            data_report += f"{db.database_id}: \n"
            if db.success:
                # Check storages one by one
                data_report += "".join(
                    [
                        f"\U00002705 {storage.storage_id}\n"
                        if storage.success is True
                        else
                        f"\U0000274C {storage.storage_id}\n"
                        for storage in db.storages
                    ])
            else:
                data_report += "\U0000274C Backup failed\n"
                data_report += f"\U000026A0 {db.output[:STRING_LIMIT]}\n"
        return data_report

    def notify(self):
        """ Convert report dict to string and send via Telegram """
        bot = telebot.TeleBot(self.config["token"])
        try:
            bot.send_message(
                chat_id=self.config["chat_id"],
                text=self._parse_report(),
            )
        except ApiTelegramException:
            log.debug(
                "Telegram API key or user_id is wrong "
                "or you forgot to press /start in your bot"
            )
