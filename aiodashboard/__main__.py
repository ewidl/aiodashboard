import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

import asyncio
import bcrypt

# from .server import start_server 
from . import start_dashboard
from .coroutine_def import CoroutineDef
from .task_target_def import TaskTargetDef
from .render.dashboard_style import GREEN_THEME

from datetime import date, datetime

# @TaskTarget()
# def h(): ...

from dataclasses import dataclass
@dataclass(order=True)
class MyID:
    id1: int
    id2: str

    def __repr__(self) -> str:
        return f'MyID / {self.id1} / {self.id2}'


@CoroutineDef(target_param='id')
# async def ping(id: str, msg: str = 'PING', sleep: int = 10) -> None:
# async def ping(id: int, msg: str = 'PING', sleep: int = 10) -> None:
# async def ping(id: MyID, msg: str = 'PING', sleep: int = 10) -> None:
# async def ping(id: MyID, msg: date, sleep: int = 10) -> None:
async def ping(id: MyID, msg: datetime, sleep: int = 10) -> None:
    while True:
        print(f'{id} --> {msg}')
        await asyncio.sleep(sleep)

class Process:

    @TaskTargetDef()
    # @staticmethod
    # @classmethod
    def targets(self) -> list:
        print(f'TARGET FUNCTION CLASS = {self.__class__.__qualname__}')
        # return ['ABC', 'DEF', 'GHI', 'XYZ']
        # return [1, 2, 3, 4]
        return [MyID(1, 'A'), MyID(2, 'B'), MyID(3, 'C'), MyID(4, 'D')]

    @CoroutineDef(target_param='id')
    # async def ping(self, id: str, msg: str, sleep: float = 10) -> None:
    # async def ping(self, id: int, msg: str, sleep: float = 10) -> None:
    async def ping(self, id: MyID, msg: str, sleep: float = 10) -> None:
        while True:
            print(f'{msg} / sleep {sleep} ### {self.targets()}')
            await asyncio.sleep(sleep)

def hash_password(password: str) -> bytes:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt)

if __name__ == '__main__':

    loop = asyncio.get_event_loop()

    pwd_hash = hash_password('TEST')

    proc = Process()

    try:
        # Start the dashboard.
        start_dashboard(loop=loop, pwd_hash=pwd_hash, process=proc, 
                        use_plain_html=False, style=GREEN_THEME)

        # Start the ping task.
        # loop.create_task(ping(id='ABC'))
        # loop.create_task(ping(id=1))
        # loop.create_task(ping(id=MyID(1,'A')))
        # loop.create_task(ping(id=MyID(1,'A'), msg=date.today()))
        loop.create_task(ping(id=MyID(1,'A'), msg=datetime.now()))
        # loop.create_task(ping(id='XYZ',msg='PONG'))
        # loop.create_task(proc.ping(id='XYZ',msg='PONG'))
        # loop.create_task(proc.ping(id=4,msg='PONG'))
        loop.create_task(proc.ping(id=MyID(4,'D'),msg='PONG'))

        # Enter the event loop.
        loop.run_forever()
    except KeyboardInterrupt:
        print('EXIT')
    finally:
        pass