from aiohttp_session import setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from cryptography import fernet
import base64

from .typing import WebHandler

def setup_cookie_storage(
        app: WebHandler
    ) -> None:
    """
    Setup for encrypted cookie storage.
    Uses the fernet method (symmetric-key encryption).
    """
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    setup(
        app, 
        EncryptedCookieStorage(secret_key)
    )
