from typing import Awaitable, Callable

import asyncio
Loop = asyncio.AbstractEventLoop

from aiohttp import web
WebHandler = Callable[..., Awaitable[web.StreamResponse]]
