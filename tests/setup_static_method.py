import asyncio
from aiodashboard.coroutine_def import CoroutineDef
from aiodashboard.task_target_def import TaskTargetDef

class Process:

    @staticmethod
    @TaskTargetDef()
    def targets() -> list:
        return ["IJK", "LMN"]

    @staticmethod
    @CoroutineDef(target_param="id")
    async def ping(id: str, msg: str = "PING", sleep: int = 10) -> None:
        while True:
            print(f"{id} --> {msg}")
            await asyncio.sleep(sleep)
