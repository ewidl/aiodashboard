from typing import Awaitable, Callable # type: ignore

import asyncio
Loop = asyncio.AbstractEventLoop # type: ignore

from aiohttp import web
WebHandler = Callable[[web.Request], Awaitable[web.StreamResponse]] # type: ignore
