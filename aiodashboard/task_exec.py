from __future__ import annotations

from asyncio import Task

from typing import Any, Optional
from inspect import getcallargs
from collections import OrderedDict

from .coroutine_def import CoroutineDef
from .task_exec_info import TaskExecInfo
from .util import all_tasks, task_id as str_task_id, get_package_name

class TaskExec:

    __cache: dict[Task, Optional[TaskExecInfo]] = dict()

    @staticmethod
    def get_all() -> list[TaskExecInfo]:
        """
        Retrieve info for all running tasks.
        Relevant tasks are identfied via the 'CoroutineDef' decorator.
        For other tasks, no info is returned.
        """
        all_exec_infos = []

        for task in all_tasks():
            info = TaskExec.get(task=task)
            if info: all_exec_infos.append(info)

        return all_exec_infos

    @staticmethod
    def get(task: Task[Any]) -> Optional[TaskExecInfo]:
        """
        Retrieve info for a running task.
        Relevant tasks are identfied via the 'TaskDef' decorator.
        For other tasks, `None` is returned as info.
        """
        exec_info = TaskExec.__cache.get(task)
        if exec_info: return exec_info

        # Get stack frames for this task's coroutine.
        stack = task.get_stack()
        for frame in stack:
            package_name = frame.f_globals['__package__']
            coroutine_name = frame.f_code.co_name

            # Check if the 'coroutine_def_wrapper' decorator has been applied to the task's coroutine.
            if package_name == get_package_name() and coroutine_name == 'coroutine_def_wrapper':
                # Get function object.
                func = frame.f_locals['func']

                # Retrieve task parameters.
                args = frame.f_locals['args']
                kwargs = frame.f_locals['kwargs']
                params = getcallargs(func, *args, **kwargs)

                # Generate and append task execution info.
                exec_info = TaskExecInfo(
                    task_id=str_task_id(task),
                    coroutine_name=func.__qualname__, 
                    module=func.__module__, 
                    params=OrderedDict(sorted(params.items())),
                )

        TaskExec.__cache[task] = exec_info
        task.add_done_callback(TaskExec.__remove_from_cache)

        return exec_info

    @staticmethod
    def get_by_id(task_id: str, from_cache: bool = False) -> Optional[TaskExecInfo]:
        """
        Retrieve info for a running task by its ID.
        Relevant tasks are identfied via the 'TaskDef' decorator.
        For other tasks, `None` is returned as info.
        """
        if from_cache:
            for task, info in TaskExec.__cache.items():
                if task_id == str_task_id(task): return info
            raise RuntimeError(f'No task with ID "{task_id}" has been found in the internal cache.')
        else:
            for task in all_tasks():
                if task_id == str_task_id(task): return TaskExec.get(task)
            raise RuntimeError(f'No task with ID "{task_id}" has been found.')

    @staticmethod
    def cancel(task_id: str, target: Any, coroutine_id: str) -> None:
        for task in all_tasks():
            if task_id == str_task_id(task):
                def_info = CoroutineDef.get_coroutine_def_info(coroutine_id)
                exec_info = TaskExec.get(task)
                check_target = exec_info.params[def_info.target_param] == target
                if check_target:
                    task.cancel()
                    return
                else:
                    raise RuntimeError(f'Incorrect target ("{target}")')
        raise RuntimeError(f'No task with ID = "{task_id}" found')

    @staticmethod
    def __remove_from_cache(t: Task[Any]) -> None:
        del TaskExec.__cache[t]

    # @staticmethod
    # def __print_cache() -> None:
    #     print('### TASK INFO CACHE ###')
    #     for task, info in TaskExec.__cache.items(): print(f'\t{task.get_name()}: {info}')
