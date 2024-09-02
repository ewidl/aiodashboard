from aiohttp import web
import aiohttp_session

from .login_status import LoginStatus
from ..util.typing import WebHandler

@web.middleware
async def check_login(
        request: web.Request, 
        handler: WebHandler
    ) -> web.StreamResponse:
    """
    Middleware for checking the login status.
    """
    # Check if login is requried for this page.
    require_login = getattr(handler, '__require_login__', False)
    if require_login:
        # Retrieve session.
        session = await aiohttp_session.get_session(request)

        # Retrieve login status.
        login_status = session.get('login_status', LoginStatus.LOGGED_OUT)

        # Redirect to login page if not logged in.
        if login_status != LoginStatus.LOGGED_IN:
            raise web.HTTPSeeOther(location='/login')

    return await handler(request)

