from typing import Callable

from dataclasses import dataclass
from lazy import lazy

from .util import coroutine_id
from .callable_code_context import CallableCodeContext

@dataclass
class CoroutineDefInfo:
    """
    Provide information about a coroutine.
    """
    func: Callable
    func_name: str
    module: str
    target_param: str
    coroutine_id: str
    context: CallableCodeContext

    def __init__(self, func: Callable, target_param: str) -> None:
        self.func=func
        self.func_name=func.__qualname__
        self.module=func.__module__
        self.target_param=target_param
        self.coroutine_id=coroutine_id(self.func_name, self.module)

    @lazy
    def context(self) -> CallableCodeContext:
        """
        Return the context of the coroutine.
        This must be a lazily evaluated attribute to avoid infinite recursion at parsing time.
        """
        return CallableCodeContext.get(self.func)
