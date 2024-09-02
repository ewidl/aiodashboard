import asyncio
from aiodashboard.coroutine_def import CoroutineDef
from aiodashboard.task_target_def import TaskTargetDef

class Process:

    @classmethod
    @TaskTargetDef()
    def targets(self) -> list:
        return ["DEF", "GHI"]

    @classmethod
    @CoroutineDef(target_param="id")
    async def ping(cls, id: str, msg: str = "PING", sleep: int = 10) -> None:
        while True:
            print(f"{id} --> {msg}")
            await asyncio.sleep(sleep)
