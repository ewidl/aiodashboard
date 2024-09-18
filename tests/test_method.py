import pytest
import pytest_asyncio

from typing import Any
from types import ModuleType
from collections.abc import AsyncGenerator

import asyncio

from .base import Base, CoroutineDef, TaskTargetDef

class TestMethod(Base):

    SETUP_MODULE: str = "tests.setup_method"
    COROUTINE_NAME: str = "Process.ping"
    COROUTINE_HAS_PARAM_SELF: bool = True
    ALL_TARGETS: list[str] = ["UVW", "XYZ"]

    @pytest.fixture(scope="module")
    def process(self, setup: ModuleType) -> Any:
        yield setup.Process()

    @pytest.fixture
    def task_params(self, target: Any) -> dict[str, Any]:
        return dict(id=target, msg="PING", sleep=10)

    @pytest_asyncio.fixture(loop_scope="module")
    async def task(
        self,
        current_loop: asyncio.AbstractEventLoop,
        process: Any,
        task_params: dict[str, Any],
    ) -> AsyncGenerator[asyncio.Task, None, None]:
        task = current_loop.create_task(process.ping(**task_params))
        try:
            yield task
        finally:
            if not task.cancelled():
                task.cancel()

    def test_get_target_context(self, setup: ModuleType) -> None:
        context = TaskTargetDef.get_context()
        assert context.is_function == False
        assert context.is_method == True
        assert context.is_static_method == False
        assert context.is_class_method == False
        assert context.containing_class == setup.Process
        assert len(context.parameters) == 1
        assert "self" in context.parameters
        assert context.return_annotation == list
        assert context.typeInfo() == "method of class Process"

    def test_coroutine_def_info(self, setup: ModuleType) -> None:
        ids = CoroutineDef.get_coroutine_ids()
        info = CoroutineDef.get_coroutine_def_info(ids[0])
        assert info.func == setup.Process.ping
        assert info.func_name == self.COROUTINE_NAME
        assert info.module == self.SETUP_MODULE
        assert info.target_param == setup.TASK_TARGET_PARAM

        coroutine_params = ["id", "msg", "sleep"]
        coroutine_param_types = [str, str, int]

        context = info.context
        assert context.is_function == False
        assert context.is_method == True
        assert context.is_static_method == False
        assert context.is_class_method == False
        assert context.containing_class == setup.Process
        assert len(context.parameters) == 1 + len(coroutine_params)
        assert "self" in context.parameters
        for p, t in zip(coroutine_params, coroutine_param_types):
            assert p in context.parameters
            assert context.parameters[p].annotation == t
        assert context.return_annotation == None
        assert context.typeInfo() == "method of class Process"
