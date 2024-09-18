from enum import IntEnum

class LoginStatus(IntEnum):
    """
    Status codes for login status.
    """
    LOGGED_OUT = 0
    LOGGED_IN = 1
    FAILED = 2
