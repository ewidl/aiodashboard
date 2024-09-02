from typing import Callable

from dataclasses import dataclass
from lazy import lazy

from .util import coroutine_id
from .callable_code_context import CallableCodeContext

@dataclass
class CoroutineDefInfo:
    func: Callable
    func_name: str
    module: str
    target_param: str
    context: CallableCodeContext

    def __init__(self, func: Callable, target_param: str) -> None:
        self.func=func
        self.func_name=func.__qualname__
        self.module=func.__module__
        self.target_param=target_param

    @lazy
    def context(self) -> CallableCodeContext:
        return CallableCodeContext.get(self.func)

    @property
    def coroutine_id(self) -> str:
        return coroutine_id(self.func_name, self.module)
