import pytest
import pytest_asyncio

from typing import Any
from types import ModuleType
from collections.abc import AsyncGenerator

import asyncio

from .base import Base, CoroutineDef, TaskTargetDef

class TestFunction(Base):

    SETUP_MODULE: str = "tests.setup_function"
    COROUTINE_NAME: str = "ping"
    ALL_TARGETS: list[str] = ["ABC", "DEF"]

    @pytest.fixture(scope="module")
    def process(self, setup: ModuleType) -> Any:
        return None

    @pytest.fixture
    def task_params(self, target: Any) -> dict[str, Any]:
        return dict(id=target, msg="PING", sleep=10)

    @pytest_asyncio.fixture(loop_scope="module")
    async def task(
        self,
        setup: ModuleType,
        current_loop: asyncio.AbstractEventLoop,
        task_params: dict[str, Any],
    ) -> AsyncGenerator[asyncio.Task, None, None]:
        task = current_loop.create_task(setup.ping(**task_params))
        try:
            yield task
        finally:
            if not task.cancelled(): task.cancel()

    def test_get_target_context(self) -> None:
        context = TaskTargetDef.get_context()
        assert context.is_function == True
        assert context.is_method == False
        assert context.is_static_method == False
        assert context.is_class_method == False
        assert context.containing_class == None
        assert len(context.parameters) == 0
        assert context.return_annotation == list
        assert context.typeInfo() == None

    def test_coroutine_def_info(self, setup: ModuleType) -> None:
        ids = CoroutineDef.get_coroutine_ids()
        info = CoroutineDef.get_coroutine_def_info(ids[0])
        assert info.func == setup.ping
        assert info.func_name == self.COROUTINE_NAME
        assert info.module == self.SETUP_MODULE
        assert info.target_param == "id"

        coroutine_params = ["id", "msg", "sleep"]
        coroutine_param_types = [str, str, int]

        context = info.context
        assert context.is_function == True
        assert context.is_method == False
        assert context.is_static_method == False
        assert context.is_class_method == False
        assert context.containing_class == None
        assert len(context.parameters) == len(coroutine_params)

        for p, t in zip(coroutine_params, coroutine_param_types):
            assert p in context.parameters
            assert context.parameters[p].annotation == t
        assert context.return_annotation == None
        assert context.typeInfo() == None
