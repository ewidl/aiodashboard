import asyncio
from aiodashboard.coroutine_def import CoroutineDef
from aiodashboard.task_target_def import TaskTargetDef

from .custom_id import CustomID

"""Just like the setup from setup_static_method.py, but with a custom target ID."""

TASK_TARGET_PARAM: str = "id"

class Process:

    @TaskTargetDef()
    @staticmethod
    def targets() -> list:
        return [CustomID(1, 'A'), CustomID(2, 'B'), CustomID(3, 'C'), CustomID(4, 'D')]

    @CoroutineDef(target_param=TASK_TARGET_PARAM)
    @staticmethod
    async def ping(id: CustomID, msg: str = "PING", sleep: int = 10) -> None:
        while True:
            print(f"{id} --> {msg}")
            await asyncio.sleep(sleep)
