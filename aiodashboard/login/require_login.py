from ..util.typing import WebHandler

def require_login(func: WebHandler) -> WebHandler:
    """
    Decorator for endpoints that require a login.
    """
    func.__require_login__ = True  # type: ignore
    return func
