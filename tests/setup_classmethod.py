import asyncio
from aiodashboard.coroutine_def import CoroutineDef
from aiodashboard.task_target_def import TaskTargetDef

TASK_TARGET_PARAM: str = "id"

class Process:

    @TaskTargetDef()
    @classmethod
    def targets(cls) -> list:
        return ["DEF", "GHI"]

    @CoroutineDef(target_param=TASK_TARGET_PARAM)
    @classmethod
    async def ping(cls, id: str, msg: str = "PING", sleep: int = 10) -> None:
        while True:
            print(f"{id} --> {msg}")
            await asyncio.sleep(sleep)
