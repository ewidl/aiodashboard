import inspect
from typing import Any
from datetime import date, datetime

def get_type_from_str(
        param: inspect.Parameter, 
        value: str
    ) -> Any:
    """
    Convert string to type as given by parameter annotation.
    """
    if param.annotation == date:
        return date.fromisoformat(value)
    elif param.annotation == datetime:
        return datetime.fromisoformat(value)

    return param.annotation(value)
