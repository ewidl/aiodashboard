import asyncio
from aiodashboard.coroutine_def import CoroutineDef
from aiodashboard.task_target_def import TaskTargetDef

"""Just like the setup from setup_static_method.py, but without stacked staticmethod decorators."""

TASK_TARGET_PARAM: str = "id"

class Process:

    @TaskTargetDef()
    def targets() -> list:
        return ["IJK", "LMN"]

    @CoroutineDef(target_param=TASK_TARGET_PARAM)
    async def ping(id: str, msg: str = "PING", sleep: int = 10) -> None:
        while True:
            print(f"{id} --> {msg}")
            await asyncio.sleep(sleep)
