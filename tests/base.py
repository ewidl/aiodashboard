import pytest
import pytest_asyncio

from unittest.mock import patch


def mock_aiohttp_jinja2_template(*args, **kwargs):
    return lambda func: func


patch("aiohttp_jinja2.template", mock_aiohttp_jinja2_template).start()

import asyncio
import importlib

from aiodashboard.coroutine_def import CoroutineDef
from aiodashboard.task_target_def import TaskTargetDef
from aiodashboard.task_exec import TaskExec
from aiodashboard.dashboard import Dashboard
from aiodashboard.util import task_id, coroutine_id

from typing import Any
from types import ModuleType
from collections.abc import Generator

from contextlib import nullcontext as does_not_raise
from aiohttp.web import HTTPSeeOther

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
    def task_target_param(self, setup: ModuleType) -> str:
        return setup.TASK_TARGET_PARAM

    @pytest.fixture(scope="module")
    def target_pos(self) -> int:
        return 0

    @pytest.fixture(scope="module")
    def target(self, all_targets: list[Any], target_pos: int) -> Any:
        return all_targets[target_pos]

    @pytest_asyncio.fixture(loop_scope="module")
    async def current_loop(self) -> asyncio.AbstractEventLoop:
        return asyncio.get_running_loop()

    def test_task_target_check(self, process: Any, all_targets: list[Any]) -> None:
        with does_not_raise():
            TaskTargetDef.check()

    def test_get_targets(self, process: Any, all_targets: list[Any]) -> None:
        targets = TaskTargetDef.get_targets(process=process)
        assert targets == all_targets

    def test_coroutine_def_check(self, process: Any, all_targets: list[Any]) -> None:
        with does_not_raise():
            CoroutineDef.check()

    def test_coroutine_ids(self) -> None:
        ids = CoroutineDef.get_coroutine_ids()
        assert len(ids) == 1

    @pytest.mark.asyncio(loop_scope="module")
    async def test_coroutine_defs(self) -> None:
        defs = CoroutineDef.get_coroutine_defs()
        assert len(defs) == 1

    @pytest.mark.asyncio(loop_scope="module")
    async def test_coroutine_def_start_task(self, process: Any, current_loop: asyncio.AbstractEventLoop) -> None:
        str_coroutine_id = coroutine_id(self.COROUTINE_NAME, self.SETUP_MODULE)
        coroutine_def = CoroutineDef.get_coroutine_def_info(str_coroutine_id)
        param_apply = {"id": self.ALL_TARGETS[0], "msg": "TEST", "sleep": 10}

        # Check that no task is running now.
        assert 0 == len(TaskExec.get_all())

        # Start a task based on info from coroutine def.
        if coroutine_def.context.is_method:
            task = current_loop.create_task(coroutine_def.func(process, **param_apply))
        else:
            task = current_loop.create_task(coroutine_def.func(**param_apply))

        # Check that exactly 1 task is running now.
        await asyncio.sleep(0.1)
        assert 1 == len(TaskExec.get_all())
        assert False == task.done()

        # Cancel task.
        with pytest.raises(asyncio.CancelledError):
            task.cancel()
            await task

        # Check that again no task is running.
        assert 0 == len(TaskExec.get_all())


    @pytest.mark.asyncio(loop_scope="module")
    async def test_coroutine_call(self) -> None:
        for _, c_def in CoroutineDef.get_coroutine_defs().items():
            if c_def.context.is_method:
                with pytest.raises(
                    TypeError, match="missing 2 required positional argument"
                ):
                    await c_def.func()
            else:
                with pytest.raises(
                    TypeError, match="missing 1 required positional argument"
                ):
                    await c_def.func()

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

    @pytest.mark.asyncio(loop_scope="module")
    async def test_dashboard_index(
        self, task: asyncio.Task, process: Any, target_pos: int
    ) -> None:
        dashboard = Dashboard(pwd_hash=None, process=process)

        response = await dashboard.index(None)

        coroutine_defs = response["coroutine_defs"]
        assert 1 == len(coroutine_defs)
        cd_coroutine_id = list(coroutine_defs.keys())[0]
        cd_coroutine_def = list(coroutine_defs.values())[0]
        assert cd_coroutine_id == coroutine_id(self.COROUTINE_NAME, self.SETUP_MODULE)

        task_display_info = response["task_display_info"]
        assert 1 == len(task_display_info)
        (
            tdi_target,
            tdi_target_pos,
            tdi_coroutine_name,
            tdi_module,
            tdi_task_id,
            tdi_coroutine_id,
            tdi_params,
            tdi_type_info,
        ) = task_display_info[0]

        assert tdi_task_id == task_id(task)
        assert tdi_target_pos == target_pos
        assert cd_coroutine_id == tdi_coroutine_id
        assert cd_coroutine_def.func_name == tdi_coroutine_name
        assert cd_coroutine_def.module == tdi_module

        task_targets = response["task_targets"]
        assert task_targets == self.ALL_TARGETS
        assert task_targets[tdi_target_pos] == tdi_target

    @pytest.mark.asyncio(loop_scope="module")
    async def test_dashboard_cancel_task(
        self, task: asyncio.Task, process: Any, target_pos: int
    ) -> None:
        dashboard = Dashboard(pwd_hash=None, process=process)

        response = await dashboard.index(None)
        coroutine_defs = response["coroutine_defs"]
        cd_coroutine_id = list(coroutine_defs.keys())[0]
        cd_coroutine_def = list(coroutine_defs.values())[0]

        class DummyCancelTaskRequest:
            query = {
                "target-pos": target_pos,
                "task-id": task_id(task),
                "coroutine-id": cd_coroutine_id,
            }

        response = await dashboard.cancel_task(DummyCancelTaskRequest())
        assert response["target"] == self.ALL_TARGETS[target_pos]
        assert response["target_pos"] == target_pos
        assert response["func_name"] == cd_coroutine_def.func_name
        assert response["module"] == cd_coroutine_def.module
        assert response["task_id"] == task_id(task)
        assert response["coroutine_id"] == cd_coroutine_id

    @pytest.mark.asyncio(loop_scope="module")
    async def test_dashboard_cancel_task_apply(
        self, task: asyncio.Task, process: Any, target_pos: int
    ) -> None:
        dashboard = Dashboard(pwd_hash=None, process=process)

        response = await dashboard.index(None)
        coroutine_defs = response["coroutine_defs"]
        cd_coroutine_id = list(coroutine_defs.keys())[0]

        class DummyCancelTaskApplyRequest:
            async def post(self):
                return {
                    "target-pos": target_pos,
                    "task-id": task_id(task),
                    "coroutine-id": cd_coroutine_id,
                }

        with pytest.raises(HTTPSeeOther, match="See Other"):
            await dashboard.cancel_task_apply(DummyCancelTaskApplyRequest())

        with pytest.raises(asyncio.CancelledError):
            await task

        assert task.cancelled()

    @pytest.mark.asyncio(loop_scope="module")
    async def test_dashboard_start_task(
        self, task: asyncio.Task, process: Any, target_pos: int, task_target_param: str
    ) -> None:
        dashboard = Dashboard(pwd_hash=None, process=process)

        response = await dashboard.index(None)
        coroutine_defs = response["coroutine_defs"]
        cd_coroutine_id = list(coroutine_defs.keys())[0]

        class DummyStartTaskRequest:
            query = {"target-pos": target_pos, "coroutine-id": cd_coroutine_id}

        response = await dashboard.start_task(DummyStartTaskRequest())

        assert response["coroutine_id"] == cd_coroutine_id
        assert response["target_param"] == task_target_param
        assert response["target"] == self.ALL_TARGETS[target_pos]
        assert response["target_pos"] == target_pos

        coroutine_params = dict(msg=str, sleep=int)
        params = response["params"]

        assert len(params) == len(coroutine_params)

        for param in params:
            if param.name in ["self", "cls"]:
                continue
            assert param.name in coroutine_params
            assert param.annotation == coroutine_params[param.name]

    @pytest.mark.asyncio(loop_scope="module")
    async def test_dashboard_start_task_apply(
        self, process: Any, target_pos: int, task_target_param: str
    ) -> None:
        dashboard = Dashboard(pwd_hash=None, process=process)

        response = await dashboard.index(None)
        coroutine_defs = response["coroutine_defs"]
        cd_coroutine_id = list(coroutine_defs.keys())[0]

        class DummyStartTaskApplyRequest:
            async def post(self):
                return {
                    "target-pos": target_pos,
                    "target-param": task_target_param,
                    "coroutine-id": cd_coroutine_id,
                    "msg": "TEST",
                    "sleep": 100,
                }

        n_tasks = len(TaskExec.get_all())

        with pytest.raises(HTTPSeeOther, match="See Other"):
            await dashboard.start_task_apply(DummyStartTaskApplyRequest())

        assert len(TaskExec.get_all()) == n_tasks + 1
