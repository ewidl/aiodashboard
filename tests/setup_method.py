import asyncio
from aiodashboard.coroutine_def import CoroutineDef
from aiodashboard.task_target_def import TaskTargetDef

TASK_TARGET_PARAM: str = "id"

class Process:

    @TaskTargetDef()
    def targets(self) -> list:
        return ["UVW", "XYZ"]

    @CoroutineDef(target_param=TASK_TARGET_PARAM)
    async def ping(self, id: str, msg: str = "PING", sleep: int = 10) -> None:
        while True:
            print(f"{id} --> {msg}")
            await asyncio.sleep(sleep)
