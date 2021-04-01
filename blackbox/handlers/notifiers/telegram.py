from blackbox.handlers.notifiers._base import BlackboxNotifier
import telebot


class Telegram(BlackboxNotifier):
    required_fields = ("token", "chat_id",)

    def _parse_report(self) -> dict:
        return {
            "output": self.report.output,
            "report": self.report,
        }

    def notify(self):
        report = self._parse_report()["report"]
        welcome_message = 'Blackbox Backup Status:\n'
        databases_report = [f'{db.database_id} \U00002705\n' for db in
                            report.databases if db.success is True]
        bot = telebot.TeleBot(self.config["token"])
        return bot.send_message(chat_id=self.config["chat_id"],
                                text=welcome_message + "".join(
                                    databases_report))
