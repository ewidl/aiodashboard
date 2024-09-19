from __future__ import annotations

import importlib
from typing import Any, Callable, Optional
from types import FunctionType, MethodType
from inspect import getattr_static, signature, Parameter

from dataclasses import dataclass, field
from collections import OrderedDict

@dataclass(frozen=True)
class CallableCodeContext:
    """
    Provide the context of a callable from its code.
    Determine if the callable is an ordinary function, a method, a static method, or a class method.
    If it is a (ordinary/static/class) method, provide the class it is defined in.
    Retrieve the list of parameters (function signature) and its return type.
    """
    is_function: bool = False
    is_method: bool = False
    is_static_method: bool = False
    is_class_method: bool = False
    containing_class: Optional[type] = None
    parameters: OrderedDict[str, Parameter] = field(default_factory=OrderedDict)
    return_annotation: Any = None

    def __post_init__(self) -> None:
        """
        Make a sanity check after initialization.
        """
        callable_type = [self.is_function, self.is_method, self.is_static_method, self.is_class_method]
        n_callable_type = callable_type.count(True)

        if n_callable_type == 0:
            raise RuntimeError('No type specified for callable code context')
        elif n_callable_type > 1:
            raise RuntimeError('Multiple types specified for callable code context')
        elif any(callable_type[1:]) and not self.containing_class:
            raise RuntimeError('No containing class specified for callable code context')

    def typeInfo(self) -> Optional[str]:
        """
        For (ordinary/static/class) methods, return a string with information about their
        type and the class they are defined in. For ordinary functions return None.
        """
        # Note: Ignore errors of type "union-attr", because for (ordinary/static/class) methods the
        # attribute "containing_class" will not be None.
        if self.is_method:
            return f'method of class {self.containing_class.__qualname__}' # type: ignore[union-attr]
        elif self.is_static_method:
            return f'static method of class {self.containing_class.__qualname__}' # type: ignore[union-attr]
        elif self.is_class_method:
            return f'class method of class {self.containing_class.__qualname__}' # type: ignore[union-attr]
        else: # self.is_function:
            return None

    @staticmethod
    def get(func: Callable) -> CallableCodeContext:
        """
        Provide the context of a callable from its code.
        """
        # Get the qualified name of the callable and split it into parts.
        qualname_parts = func.__qualname__.split('.')

        # Retrieve the module implementing this callable.
        module = importlib.import_module(func.__module__)

        # Create hierarchical lists of objects/types that contain the definition of the callable.
        code_objects = [getattr(module, qualname_parts[0])]
        types = [type(code_objects[0])]
        for qp in qualname_parts[1:]:
            if qp == '<locals>':
                raise RuntimeError(f'Classes / functions nested inside functions are not supported: {func.__qualname__}')

            code_objects.append(getattr(code_objects[-1], qp))
            types.append(type(code_objects[-1]))

        # Sanity check: Is this really a callable?
        if not callable(code_objects[-1]): raise RuntimeError(f'{func.__qualname__} is not a callable')

        callable_name = qualname_parts[-1]
        callable_type = types[-1]

        # Retrieve the list of parameters (function signature) and its return type.
        sig = signature(code_objects[-1])
        target_params = OrderedDict(sorted(sig.parameters.items()))
        return_annotation = sig.return_annotation

        is_function = (callable_type is FunctionType) # Callable is a function.
        # is_method = (target_type is MethodType) # Callable is a method.
        is_wrapped = hasattr(code_objects[-1], '__wrapped__') # Callable is wrapped by a decorator.

        # Plain function: not defined within another scope.
        if 1 == len(types) and is_function:
            return CallableCodeContext(is_function=True,
                parameters=target_params,
                return_annotation=return_annotation
                )

        # Get the containing scope.
        containing_scope = code_objects[-2]
        containing_scope_type = types[-2]

        if containing_scope_type is type:
            # Function is a class method.
            if isinstance(getattr_static(containing_scope, callable_name), classmethod) or \
                (is_wrapped and isinstance(getattr(code_objects[-1], '__wrapped__'), classmethod)):
                return CallableCodeContext(
                    is_class_method=True,
                    containing_class=containing_scope,
                    parameters=target_params,
                    return_annotation=return_annotation
                )

            # Function is a static method.
            if isinstance(getattr_static(containing_scope, callable_name), staticmethod) or \
                (is_wrapped and isinstance(getattr(code_objects[-1], '__wrapped__'), staticmethod)):
                return CallableCodeContext(
                    is_static_method=True,
                    containing_class=containing_scope,
                    parameters=target_params,
                    return_annotation=return_annotation
                )

            # Special case of a static method (method defined without self argument).
            if 'self' not in target_params:
                return CallableCodeContext(
                    is_static_method=True,
                    containing_class=containing_scope,
                    parameters=target_params,
                    return_annotation=return_annotation
                )

            # Default case: ordinary method.
            return CallableCodeContext(
                is_method=True,
                containing_class=containing_scope,
                parameters=target_params,
                return_annotation=return_annotation
            )

        raise RuntimeError(f'code context for {func.__qualname__} was not properly determined')
