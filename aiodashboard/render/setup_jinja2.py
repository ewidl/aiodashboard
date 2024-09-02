from aiohttp_jinja2 import setup, get_env
from jinja2 import FileSystemLoader

from pathlib import Path
from datetime import datetime
from dataclasses import asdict
import socket
import inspect

from .dashboard_style import DashboardStyle
from ..util.typing import WebHandler

def setup_jinja2(
        app: WebHandler,
        dashboard_name: str,
        style: DashboardStyle,
        use_plain_html: bool = False,
    ) -> None:
    """
    Setup for jinja2 template renderer.
    """
    # Select path for rendering templates.
    templates_path = str(Path(__file__).parent / 'templates' / 'plain') \
        if use_plain_html else str(Path(__file__).parent / 'templates' / 'bootstrap')

    # Basic setup for jinja2 templating engine. 
    setup(
        app,
        loader = FileSystemLoader(templates_path)
        )

    env = get_env(app)

    # Add Python's built-in function 'enumerate' to jinja2 environment.
    env.globals.update(enumerate=enumerate)

    # Add function 'datetime.now' from Python package 'datetime' to jinja2 environment.
    env.globals.update(datetime_now=datetime.now)

    # Add dashboard name to jinja2 environment.
    env.globals.update(dashboard_name=dashboard_name)

    # Add host name to jinja2 environment.
    env.globals.update(hostname=socket.gethostname())

    # Add marker to specify absence of default values and annotations.
    env.globals.update(no_default_param=inspect.Parameter.empty)

    # Add colors from dashboard style.
    env.globals.update(
        {k: f'#{v.to_hex().value}' for (k, v) in asdict(style).items()}
        )