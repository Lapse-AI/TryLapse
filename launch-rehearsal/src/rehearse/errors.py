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


class BrowserStepError(RehearseError):
    """Generic browser step failure (non-timeout)."""


def classify_step_error(exc: BaseException) -> str:
    """Map an exception to a stable error type name for step outcomes."""
    if isinstance(exc, RehearseError):
        return type(exc).__name__
    name = type(exc).__name__
    if name == "TimeoutError" or "Timeout" in name or "timeout" in str(exc).lower():
        return "BrowserStepTimeout"
    return "BrowserStepError"
