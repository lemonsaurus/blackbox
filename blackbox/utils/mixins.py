from blackbox.config import Blackbox as CONFIG
from blackbox.utils.logger import log


class SanitizeReportMixin:
    """
    Mixin class helper to mask all sensitive credentials

    Could handle any string with sensitive output
    """

    def sanitize_output(self, sensitive_output: str) -> str:
        """ Replace all self.config credentials with in any str *** """

        # first of all let's combine list of secrets from config
        sensitive_words = []
        mixed_secrets = [CONFIG.databases.values(), CONFIG.storage.values(),
                         CONFIG.notifiers.values(), ]
        for mixed_secret in mixed_secrets:
            self.extract_secrets(sensitive_words, mixed_secret)

        # now it's time to mask all secrets in our output
        for sensitive_word in set(sensitive_words):
            sensitive_output = sensitive_output.replace(
                sensitive_word, "*" * len(sensitive_word))

        # emphasize output is clear now
        sanitized_output = sensitive_output
        log.success("Secrets are masked!")
        return sanitized_output

    @staticmethod
    def extract_secrets(sensitive_words: [], mixed_secret) -> str:
        """ Helper method to get secrets values only """
        for database_name in mixed_secret:
            for secrets in database_name.values():
                sensitive_words += list(secrets.values())
        return sensitive_words
