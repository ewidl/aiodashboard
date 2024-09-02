import pytest
import pytest_asyncio

import asyncio
import importlib

from aiodashboard.coroutine_def import CoroutineDef
from aiodashboard.task_target_def import TaskTargetDef
from aiodashboard.task_exec import TaskExec
from aiodashboard.util import task_id, coroutine_id

from typing import Any
from types import ModuleType
from collections.abc import Generator

class Base:

    SETUP_MODULE: str
    ALL_TARGETS: list[str]
    COROUTINE_NAME: str
    COROUTINE_HAS_PARAM_SELF: bool = False
    COROUTINE_HAS_PARAM_CLS: bool = False

    @pytest.fixture(scope="module", autouse=True)
    def setup(self) -> Generator[ModuleType, None, None]:
        try:
            yield importlib.import_module(self.SETUP_MODULE)
        finally:
            CoroutineDef.reset()
            TaskTargetDef.reset()

    @pytest.fixture(scope="module")
    def all_targets(self) -> list[Any]:
        return self.ALL_TARGETS

    @pytest.fixture(scope="module")
    def target(self, all_targets: list[Any]) -> Any:
        return all_targets[0]

    @pytest_asyncio.fixture(loop_scope="module")
    async def current_loop(self) -> asyncio.AbstractEventLoop:
        return asyncio.get_running_loop()

    def test_get_targets(self, process: Any, all_targets: list[Any]) -> None:
        targets = TaskTargetDef.get_targets(process=process)
        assert targets == all_targets

    def test_coroutine_ids(self) -> None:
        ids = CoroutineDef.get_coroutine_ids()
        assert len(ids) == 1

    def test_coroutine_defs(self) -> None:
        defs = CoroutineDef.get_coroutine_defs()
        assert len(defs) == 1

    @pytest.mark.asyncio(loop_scope="module")
    async def test_task_exec_get_all(
        self, target: Any, task: asyncio.Task, task_params: dict[str, Any]
    ) -> None:
        all_task_exec_infos = TaskExec.get_all()
        assert len(all_task_exec_infos) == 1

        task_exec_info = all_task_exec_infos[0]
        assert task_exec_info.task_id == task_id(task)
        assert task_exec_info.target == target

        assert task_exec_info.coroutine_name == self.COROUTINE_NAME
        assert task_exec_info.module == self.SETUP_MODULE

        params = task_exec_info.params

        if self.COROUTINE_HAS_PARAM_SELF:
            assert len(params) == 1 + len(task_params)
            assert "self" in params
        elif self.COROUTINE_HAS_PARAM_CLS:
            assert len(params) == 1 + len(task_params)
            assert "cls" in params
        else:
            assert len(params) == len(task_params)

        for k, v in task_params.items():
            assert k in params
            assert params[k] == v

    @pytest.mark.asyncio(loop_scope="module")
    async def test_task_exec_get_by_id(
        self, target: Any, task: asyncio.Task, task_params: dict[str, Any]
    ) -> None:
        str_task_id = task_id(task=task)
        task_exec_info = TaskExec.get_by_id(task_id=str_task_id, from_cache=False)

        assert task_exec_info.task_id == str_task_id
        assert task_exec_info.target == target
        assert task_exec_info.coroutine_name == self.COROUTINE_NAME
        assert task_exec_info.module == self.SETUP_MODULE

        params = task_exec_info.params

        if self.COROUTINE_HAS_PARAM_SELF:
            assert len(params) == 1 + len(task_params)
            assert "self" in params
        elif self.COROUTINE_HAS_PARAM_CLS:
            assert len(params) == 1 + len(task_params)
            assert "cls" in params
        else:
            assert len(params) == len(task_params)

        for k, v in task_params.items():
            assert k in params
            assert params[k] == v

    @pytest.mark.asyncio(loop_scope="module")
    async def test_task_exec_get_by_id_from_cache(
        self, target: Any, task: asyncio.Task, task_params: dict[str, Any]
    ) -> None:
        str_task_id = task_id(task=task)
        with pytest.raises(
            RuntimeError,
            match=f'No task with ID "{str_task_id}" has been found in the internal cache.',
        ):
            TaskExec.get_by_id(task_id=str_task_id, from_cache=True)

        assert TaskExec.get(
            task
        )  # TaskExecInfo for this task should be chached after this function call.

        task_exec_info = TaskExec.get_by_id(task_id=str_task_id, from_cache=True)
        assert task_exec_info.task_id == str_task_id
        assert task_exec_info.target == target
        assert task_exec_info.coroutine_name == self.COROUTINE_NAME
        assert task_exec_info.module == self.SETUP_MODULE

        params = task_exec_info.params

        if self.COROUTINE_HAS_PARAM_SELF:
            assert len(params) == 1 + len(task_params)
            assert "self" in params
        elif self.COROUTINE_HAS_PARAM_CLS:
            assert len(params) == 1 + len(task_params)
            assert "cls" in params
        else:
            assert len(params) == len(task_params)

        for k, v in task_params.items():
            assert k in params
            assert params[k] == v

    @pytest.mark.asyncio(loop_scope="module")
    async def test_task_exec_cancel(self, target: Any, task: asyncio.Task) -> None:
        str_task_id = task_id(task=task)
        str_coroutine_id = coroutine_id(self.COROUTINE_NAME, self.SETUP_MODULE)

        assert 1 == len(TaskExec.get_all())

        with pytest.raises(asyncio.CancelledError):
            TaskExec.cancel(str_task_id, target, str_coroutine_id)
            await task

        assert task.cancelled()
        assert 0 == len(TaskExec.get_all())
