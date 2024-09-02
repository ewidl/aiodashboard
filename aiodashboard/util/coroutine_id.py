def coroutine_id(
        func_name: str, 
        module: str
    ) -> str:
    """
    Define unique ID for coroutines.    
    """
    return str(hash((func_name, module)))
