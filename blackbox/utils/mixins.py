from blackbox.config import Blackbox as CONFIG
from blackbox.utils.logger import log


class SanitizeReportMixin:
    """
    Mixin class helper to mask passwords and tokens set up in blackbox.yaml.

    Could mask any string with sensitive output because it has its own
    method to get all credentials from blackbox config.
    """

    def sanitize_output(self, sensitive_output: str) -> str:
        """Replace all self.config credentials values with ***** in any string."""
        # First of all let's combine list of secrets from config.
        sensitive_words = self._extract_secrets()

        # Now it's time to mask all secrets in our output.
        for sensitive_word in set(sensitive_words):
            sensitive_output = sensitive_output.replace(str(sensitive_word), "*****")

        # Emphasize output is clear now
        sanitized_output = sensitive_output
        log.success("Secrets are masked!")
        return sanitized_output

    @staticmethod
    def _extract_secrets() -> list:
        """Helper method to get secrets values."""
        sensitive_words = []
        # Blackbox_Type -> Kind -> Unique ID (str) -> Keys and Values (passwords and tokens)
        types = [CONFIG.databases.values(), CONFIG.storage.values(), CONFIG.notifiers.values(), ]

        for blackbox_type in types:
            for kind in blackbox_type:
                for unique_id in kind.values():
                    for val in unique_id.values():
                        if isinstance(val, list):
                            sensitive_words += ",".join(val)
                        elif isinstance(val, dict):
                            sensitive_words += val.values()
                        else:
                            sensitive_words += [val]
        return sensitive_words
