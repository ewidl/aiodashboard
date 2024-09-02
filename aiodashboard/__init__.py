import aiohttp.web as web

from .dashboard import Dashboard
from .render import setup_jinja2
from .render.dashboard_style import DashboardStyle, BLUE_THEME
from .login import *
from .util import *

from typing import Any

def start_dashboard(
        loop: Loop, 
        pwd_hash: bytes,
        process: Any = None,
        dashboard_name: str = 'Asyncio Task Dashboard',
        style: DashboardStyle = BLUE_THEME,
        use_plain_html: bool = False,
    ) -> None:
    """
    Start the dashboard.
    """
    dashboard = Dashboard(pwd_hash=pwd_hash, process=process)

    app = web.Application()
    app.router.add_get('/', dashboard.index)
    app.router.add_get('/cancel-task', dashboard.cancel_task)
    app.router.add_post('/cancel-task', dashboard.cancel_task_apply)
    app.router.add_get('/start-task', dashboard.start_task)
    app.router.add_post('/start-task', dashboard.start_task_apply)
    app.router.add_get('/login', dashboard.login)
    app.router.add_post('/login', dashboard.login_apply)
    app.router.add_get('/logout', dashboard.logout)

    setup_cookie_storage(app)
    setup_jinja2(app, dashboard_name, style, use_plain_html)

    app.middlewares.append(error_handler)
    app.middlewares.append(check_login)

    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())

    site = web.TCPSite(runner)    
    loop.run_until_complete(site.start())
