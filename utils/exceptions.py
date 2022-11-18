from abc import ABC, abstractmethod

__all__ = ["WarningError", "OutputTooLargeError", "InternalError"]


class WarningError(Exception, ABC):
    """Raised when a user request is flagged as potentially malicious

    Should define __init__(self, out: str, message: str), where out is the user-facing reply
    """

    @abstractmethod
    def __init__(self, out: str, message: str):
        self.out = out
        self.message = message
        super().__init__(message)


class OutputTooLargeError(WarningError):
    """Raised when a message is too long to send to Discord"""

    def __init__(
        self,
        out="Your requested output was too large!",
        message="Maximum Discord message length exceeded",
    ):
        super().__init__(out, message)


class InternalError(Exception):
    """Raised when something has gone wrong with the source code"""

    pass
