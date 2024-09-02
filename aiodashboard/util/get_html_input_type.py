import inspect
from datetime import date, datetime

def get_html_input_type(
        param: inspect.Parameter
    ) -> str:
    """
    Return HTML input type for different Python types.
    """
    param_type = param.annotation

    if param_type == int:
        return 'number'
    elif param_type == date:
        return 'date'
    elif param_type == datetime:
        return 'datetime-local'

    # Treat as text by default.    
    return 'text'
