from typing import Any, Callable, Optional, TypeAlias
from types import FunctionType, GenericAlias
from inspect import isfunction, Signature
from warnings import warn

from .callable_code_context import CallableCodeContext
from .util import check_callable

TaskTargetDefType: TypeAlias = Callable[..., list]

class TaskTargetDef:
    """
    The dashboard relies on a dedicated function that provides a list of all possible targets of the monitored asyncio application.
    This decorator is used for marking this specific function.
    The function must not take any arguments.
    The function must return a list (declared via a function annotation).
    The dashboard won't work unless this decorator is applied to a function.
    """

    __target_func: Optional[TaskTargetDefType] = None
    __target_func_context: Optional[CallableCodeContext] = None

    def __call__(self, func: TaskTargetDefType):
        # Check if this decorator has been applied to a callable.
        check_callable(callable=func)

        # Check and warn if the decorator has been applied previously.
        if TaskTargetDef.__target_func:
            warn(
                'Overriding previously defined task target function ' +
                    f'"{TaskTargetDef.__target_func.__qualname__}" with "{func.__qualname__}"',
                RuntimeWarning, stacklevel=2
            )
            # Reset the context when overriding the task target function.
            TaskTargetDef.__target_func_context = None

        # Save a reference to the callable.
        TaskTargetDef.__target_func = func

        # Return the callable as is.
        return func

    @staticmethod
    def get_targets(process: Any = None) -> list:
        """
        Retrieve the targets using the callable marked by this decorator.
        """
        if not TaskTargetDef.__target_func:
            raise RuntimeError('task target function has not been declared.')

        # Retrieve the code context of the target function.
        context = TaskTargetDef.get_context()

        # Depending on its type, call the target function.
        if context.is_method:
            if not process:
                func_name = TaskTargetDef.__target_func.__qualname__
                raise RuntimeError(f'Function "{func_name}" is a class method, but class instance has been provided.')
            return TaskTargetDef.__target_func(process)
        elif context.is_class_method:
            return getattr(context.containing_class, TaskTargetDef.__target_func.__name__)()
        else:
            return TaskTargetDef.__target_func()

    @staticmethod
    def get_context() -> CallableCodeContext:
        """
        Retrieve (and cache) the code context for the target function.
        """
        if not TaskTargetDef.__target_func:
            raise RuntimeError('task target function has not been declared.')

        if not TaskTargetDef.__target_func_context:
            TaskTargetDef.__target_func_context = CallableCodeContext.get(TaskTargetDef.__target_func)

        return TaskTargetDef.__target_func_context

    @staticmethod
    def check() -> None:
        """
        Check the definition of the provided target function.
        The function must not take any arguments.
        The function must return a list (declared via a function annotation).
        """
        if not TaskTargetDef.__target_func:
            raise RuntimeError('task target function has not been declared.')

        context = TaskTargetDef.get_context()
        func_name = TaskTargetDef.__target_func.__qualname__

        params = context.parameters
        if (context.is_method and not 1 == len(params)) or (not context.is_method and not 0 == len(params)):
            param_names = ', '.join(params.keys())
            raise RuntimeError('Task target functions must not require input arguments, but ' +
                f'"{func_name}" has the following input parameters: {param_names}')

        return_annotation = context.return_annotation
        if return_annotation is Signature.empty:
            raise RuntimeError(f'No typing information available for return value of function "{func_name}"')
        elif return_annotation is GenericAlias and not return_annotation.__origin__ is list:
            raise RuntimeError(f'Function "{func_name}" does not return a list')
        elif not return_annotation is list:
            raise RuntimeError(f'Function "{func_name}" does not return a list')

    @staticmethod
    def reset() -> None:
        """
        Reset the internal cache.
        Mostly intended for testing.
        """
        TaskTargetDef.__target_func = None
        TaskTargetDef.__target_func_context = None
