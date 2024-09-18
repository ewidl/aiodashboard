import asyncio
from aiodashboard.coroutine_def import CoroutineDef
from aiodashboard.task_target_def import TaskTargetDef

TASK_TARGET_PARAM: str = "id"

class Process:

    @TaskTargetDef()
    @staticmethod
    def targets() -> list:
        return ["IJK", "LMN"]

    @CoroutineDef(target_param=TASK_TARGET_PARAM)
    @staticmethod
    async def ping(id: str, msg: str = "PING", sleep: int = 10) -> None:
        while True:
            print(f"{id} --> {msg}")
            await asyncio.sleep(sleep)
