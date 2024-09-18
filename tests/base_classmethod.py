import pytest
import pytest_asyncio

from typing import Any
from types import ModuleType
from collections.abc import AsyncGenerator
from inspect import Parameter

import asyncio

from .base import Base, CoroutineDef, TaskTargetDef

class BaseClassmethod(Base):

    COROUTINE_NAME: str = "Process.ping"
    COROUTINE_HAS_PARAM_CLS: bool = True

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
        setup: ModuleType,
        task_params: dict[str, Any],
    ) -> AsyncGenerator[asyncio.Task, None, None]:
        task = current_loop.create_task(setup.Process.ping(**task_params))
        try:
            yield task
        finally:
            if not task.cancelled():
                task.cancel()

    def test_get_target_context(self, setup: ModuleType) -> None:
        context = TaskTargetDef.get_context()
        assert context.is_function == False
        assert context.is_method == False
        assert context.is_static_method == False
        assert context.is_class_method == True
        assert context.containing_class == setup.Process
        assert len(context.parameters) == 0
        assert context.return_annotation == list
        assert context.typeInfo() == "class method of class Process"
