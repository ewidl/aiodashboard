from __future__ import annotations

import importlib
from typing import Any, Callable, Optional
from types import FunctionType, MethodType
from inspect import getattr_static, signature, Parameter

from dataclasses import dataclass, field
from collections import OrderedDict

@dataclass(frozen=True)
class CallableCodeContext:
    is_function: bool = False
    is_method: bool = False
    is_static_method: bool = False
    is_class_method: bool = False
    containing_class: Optional[type] = None
    parameters: OrderedDict[str, Parameter] = field(default_factory=OrderedDict)
    return_annotation: Any = None

    def __post_init__(self) -> None:
        callable_type = [self.is_function, self.is_method, self.is_static_method, self.is_class_method]
        n_callable_type = callable_type.count(True)

        if n_callable_type == 0:
            raise RuntimeError('No type specified for callable code context')
        elif n_callable_type > 1:
            raise RuntimeError('Multiple types specified for callable code context')
        elif any(callable_type[1:]) and not self.containing_class:
            raise RuntimeError('No containing class specified for callable code context')

    def typeInfo(self) -> Optional[str]:
        if self.is_method:
            return f'method of class {self.containing_class.__qualname__}'
        elif self.is_static_method:
            return f'static method of class {self.containing_class.__qualname__}'
        elif self.is_class_method:
            return f'class method of class {self.containing_class.__qualname__}'
        else: # self.is_function:
            return None

    @staticmethod
    def get(func: Callable) -> CallableCodeContext:
        qualname_parts = func.__qualname__.split('.')

        module = importlib.import_module(func.__module__)
        code_objects = [getattr(module, qualname_parts[0])]
        types = [type(code_objects[0])]

        for qp in qualname_parts[1:]:
            if qp == '<locals>':
                raise RuntimeError(f'Classes / functions nested inside functions are not supported: {func.__qualname__}')

            code_objects.append(getattr(code_objects[-1], qp))
            types.append(type(code_objects[-1]))

        if not callable(code_objects[-1]):
            raise RuntimeError(f'{func.__qualname__} is not a callable')

        target_name = qualname_parts[-1]
        target_type = types[-1]

        sig = signature(code_objects[-1])
        target_params = sig.parameters.copy()
        return_annotation = sig.return_annotation

        if 1 == len(types) and target_type is FunctionType:
            return CallableCodeContext(is_function=True, 
                parameters=target_params, 
                return_annotation=return_annotation
                )

        containing_scope = code_objects[-2]
        containing_scope_type = types[-2]

        if containing_scope_type is type:
            
            if target_type is MethodType and \
                isinstance(getattr_static(containing_scope, target_name), classmethod):
                return CallableCodeContext(
                    is_class_method=True,
                    containing_class=containing_scope, 
                    parameters=target_params, 
                    return_annotation=return_annotation
                )

            if target_type is FunctionType and \
                isinstance(getattr_static(containing_scope, target_name), staticmethod):
                return CallableCodeContext(
                    is_static_method=True, 
                    containing_class=containing_scope, 
                    parameters=target_params, 
                    return_annotation=return_annotation
                )

            if 'self' not in target_params:
                return CallableCodeContext(
                    is_static_method=True, 
                    containing_class=containing_scope, 
                    parameters=target_params, 
                    return_annotation=return_annotation
                )

            return CallableCodeContext(
                is_method=True, 
                containing_class=containing_scope, 
                parameters=target_params, 
                return_annotation=return_annotation
            )

        raise RuntimeError(f'code context for {func.__qualname__} was not properly determined')