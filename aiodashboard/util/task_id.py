from asyncio import Task

def task_id(task: Task) -> str:
    """
    Define unique ID for asyncio tasks.    
    """
    return str(id(task))
