class RehearseError(Exception):
    """Base error with stable name for CLI output."""


class ConfigError(RehearseError):
    pass


class PreflightError(RehearseError):
    pass


class SSRFBlockedError(PreflightError):
    pass


class RunBudgetExceeded(RehearseError):
    pass


class BrowserStepTimeout(RehearseError):
    pass
