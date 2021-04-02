import telebot
from telebot.apihelper import ApiTelegramException

from blackbox.handlers.notifiers._base import BlackboxNotifier
from blackbox.utils.logger import log


class Telegram(BlackboxNotifier):
    """ Telegram notifier for Blackbox """
    required_fields = ("token", "chat_id",)

    def _parse_report(self) -> dict:
        """ Telegram needs a string so we will parse it on notification """
        return {
            "report": self.report,
        }

    @staticmethod
    def append_failed_report_to(data_report, fail_message, fail_output):
        """ Cross and warning emoji for fail message report """
        data_report += f"\U0000274C {fail_message}\n"
        data_report += f"\U000026A0 {fail_output}\n"
        return data_report

    def notify(self):
        """ Convert report dict to string and send via Telegram """
        report = self._parse_report()["report"]
        welcome_message = "Blackbox Backup Status:\n"
        data_report = ""

        # If we have at least one successful report let's show it
        if report.success:
            for db in report.databases:
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
                    data_report = self.append_failed_report_to(
                        data_report,
                        fail_message="Backup failed",
                        fail_output=db.output[:2000])
        else:
            data_report = self.append_failed_report_to(
                data_report,
                fail_message="All operations failed!",
                fail_output=report.output[:2000])

        # Assign token to bot (safe operation)
        bot = telebot.TeleBot(self.config["token"])
        try:
            bot.send_message(chat_id=self.config["chat_id"],
                             text=welcome_message + data_report)
        except ApiTelegramException:
            log.debug("Telegram API key or user_id is wrong "
                      "or you forgot to press /start in your bot")
