from typing import Any
from types import FunctionType
from inspect import iscoroutinefunction

def check_callable(callable: Any, is_coroutine: bool = False) -> None:
    """
    Check if object is a callable.
    """

    is_function = (type(callable) == FunctionType)
    is_wrapped = hasattr(callable, '__wrapped__')

    if not is_function and not is_wrapped:
        raise RuntimeError(f'"{callable.__qualname__}" is not a supported callable')

    if not is_coroutine:
        if is_function and iscoroutinefunction(callable):
            raise RuntimeError(f'"{callable.__qualname__}" is a coroutine')
        elif is_wrapped and iscoroutinefunction(callable.__wrapped__):
            raise RuntimeError(f'"{callable.__qualname__}" is a coroutine')
    else:
        if is_function and not iscoroutinefunction(callable):
            raise RuntimeError(f'"{callable.__qualname__}" is not a coroutine')
        elif is_wrapped and not iscoroutinefunction(callable.__wrapped__):
            raise RuntimeError(f'"{callable.__qualname__}" is not a coroutine')
