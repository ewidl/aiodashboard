import sys
import asyncio

from typing import Any, Optional
from .typing import Loop

def all_tasks(loop: Optional[Loop] = None) -> set[asyncio.Task[Any]]:
    """
    Retrieve all asyncio tasks.
    """
    if sys.version_info >= (3, 7):
        tasks = asyncio.all_tasks(loop=loop)
    else:
        tasks = asyncio.Task.all_tasks(loop=loop)
    return tasks
