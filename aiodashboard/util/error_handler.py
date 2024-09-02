import asyncio

from aiohttp import web
from aiohttp_jinja2 import render_template

from .typing import WebHandler

@web.middleware
async def error_handler(
        request: web.Request, 
        handler: WebHandler
    ) -> web.StreamResponse:
    """
    Middleware for error handling.
    """
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except asyncio.CancelledError:
        raise
    except Exception as ex:
        return render_template(
            'error.html', 
            request, 
            {'error_text': str(ex)}, 
            status=400
        )
