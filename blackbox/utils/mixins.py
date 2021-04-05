class SanitizeReportMixin:
    @staticmethod
    def sanitize_output(config: dict, sensitive_output: str) -> str:
        """ Replace all self.config credentials with in any str *** """
        for sensitive_word in config.values():
            sensitive_output = sensitive_output.replace(
                sensitive_word, "*" * len(sensitive_word))
        sanitized_output = sensitive_output  # emphasize output is clear now
        return sanitized_output
