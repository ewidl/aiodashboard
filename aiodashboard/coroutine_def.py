import functools
import importlib
from inspect import Parameter
from typing import Callable, Optional
from types import MappingProxyType

from .coroutine_def_info import CoroutineDefInfo
from .util import check_callable, coroutine_id as str_coroutine_id

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
        # Check if this decorator has been applied to a coroutine.
        check_callable(callable=func, is_coroutine=True)

        # Get coroutuine ID.
        coroutine_id = str_coroutine_id(func.__qualname__, func.__module__)

        # Define wrapper function for coroutine.
        @functools.wraps(func)
        async def coroutine_def_wrapper(*args, **kwargs):

            # Handle special case of class method.
            if type(func) == classmethod:
                context = CoroutineDef.get_coroutine_def_info(coroutine_id).context
                return await func.__get__(None, context.containing_class)(*args, **kwargs)

            # Default case.
            return await func(*args, **kwargs)

        # Add info about this coroutine.
        info = CoroutineDefInfo(coroutine_def_wrapper, self._target_param)
        CoroutineDef.__coroutine_def_infos[coroutine_id] = info

        # Return wrapper function.
        return coroutine_def_wrapper

    @staticmethod
    def get_coroutine_ids() -> list[str]:
        """
        Get a list of the internal IDs of all known coroutine definitions.
        """
        return list(CoroutineDef.__coroutine_def_infos.keys())

    @staticmethod
    def get_coroutine_def_info(coroutine_id: str) -> Optional[CoroutineDefInfo]:
        """
        Get the coroutine info associated to the internal coroutine ID.
        If ID is unknown, return None.
        """
        return CoroutineDef.__coroutine_def_infos.get(coroutine_id)

    @staticmethod
    def get_coroutine_defs() -> MappingProxyType[str, CoroutineDefInfo]:
        """
        Get a read-only view of all known coroutine definitions (internal coroutine IDs vs. coroutine infos).
        """
        return MappingProxyType(CoroutineDef.__coroutine_def_infos)

    @staticmethod
    def check() -> None:
        """
        Check the known coroutine function definitions.
        The functions must declare typing information for all call parameters (via function annotations).
        """
        for coroutine_def_info in CoroutineDef.__coroutine_def_infos.values():
            for param in coroutine_def_info.context.parameters.values():
                if not param.name in ['self', 'cls'] and param.annotation is Parameter.empty:
                    raise RuntimeError(
                        'No typing information available for parameter ' +
                        f'"{param.name}" in function "{coroutine_def_info.func_name}"'
                    )

    @staticmethod
    def reset() -> None:
        """
        Reset the internal cache.
        Mostly intended for testing.
        """
        CoroutineDef.__coroutine_def_infos.clear()
