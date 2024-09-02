import functools
from inspect import iscoroutinefunction, Parameter
from typing import Callable, Optional
from types import MappingProxyType

from .coroutine_def_info import CoroutineDefInfo

class CoroutineDef:
    """
    Decorator for coroutine functions that the monitored asyncio application is supposed to execute.
    The dashboard won't show an executing coroutine function or let you start new tasks executing it 
    unless this decorator has been applied to the coroutine function.
    """

    __coroutine_def_infos: dict[str, CoroutineDefInfo] = dict()

    def __init__(self, target_param: str) -> None:
        self._target_param = target_param

    def __call__(self, func: Callable):

        if not iscoroutinefunction(func):
            raise RuntimeError(f'"{func.__qualname__}" is not a coroutine')

        @functools.wraps(func)
        async def coroutine_def_wrapper(*args,**kwargs):
            return await func(*args, **kwargs)

        info = CoroutineDefInfo(coroutine_def_wrapper, self._target_param)
        CoroutineDef.__coroutine_def_infos[info.coroutine_id] = info

        return coroutine_def_wrapper

    @staticmethod
    def get_coroutine_ids() -> list[str]:
        return list(CoroutineDef.__coroutine_def_infos.keys())

    @staticmethod
    def get_coroutine_def_info(coroutine_id: str) -> Optional[CoroutineDefInfo]:
        return CoroutineDef.__coroutine_def_infos.get(coroutine_id)

    @staticmethod
    def get_coroutine_defs() -> MappingProxyType[str, CoroutineDefInfo]:
        return MappingProxyType(CoroutineDef.__coroutine_def_infos)

    @staticmethod
    def check() -> None:
        for coroutine_def_info in CoroutineDef.__coroutine_def_infos.values():
            for param in coroutine_def_info.context.parameters.values():
                if not param.name == 'self' and param.annotation is Parameter.empty:
                    raise RuntimeError(
                        'No typing information available for parameter ' +
                        f'"{param.name}" in function "{coroutine_def_info.func_name}"'
                    )

    @staticmethod
    def reset() -> None:
        CoroutineDef.__coroutine_def_infos.clear()
