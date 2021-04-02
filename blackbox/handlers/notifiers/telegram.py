import telebot
from telebot.apihelper import ApiTelegramException

from blackbox.handlers.notifiers._base import BlackboxNotifier
from blackbox.utils.logger import log


class Telegram(BlackboxNotifier):
    required_fields = ("token", "chat_id",)

    def _parse_report(self) -> dict:
        return {
            "report": self.report,
        }

    def notify(self):
        report = self._parse_report()["report"]
        welcome_message = 'Blackbox Backup Status:\n'
        data_report = ''
        if report.success:
            for db in report.databases:
                data_report += f'{db.database_id}: \n'
                if db.success:
                    data_report += "".join(
                        [
                            f'\U00002705 {storage.storage_id}\n'
                            if storage.success is True
                            else
                            f'\U0000274C {storage.storage_id}\n'
                            for storage in db.storages
                        ])
                else:
                    data_report += f'\U0000274C Backup failed:\n'
                    data_report += f'\U000026A0 {db.output[:2000]}'
        else:
            data_report += f'\U0000274C All operations failed!\n'
            data_report += f'\U000026A0 {report.output[:2000]}'

        bot = telebot.TeleBot(self.config["token"])
        try:
            bot.send_message(chat_id=self.config["chat_id"],
                             text=welcome_message + data_report)
        except ApiTelegramException:
            log.debug('Telegram API key or user_id is wrong '
                      'or you forgot to press /start in your bot')
