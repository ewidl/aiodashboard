import pytest
import pytest_asyncio

from typing import Any
from types import ModuleType
from collections.abc import AsyncGenerator

import asyncio

from .base import Base, CoroutineDef, TaskTargetDef

class BaseStaticmethod(Base):

    COROUTINE_NAME: str = "Process.ping"

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
        assert context.is_static_method == True
        assert context.is_class_method == False
        assert context.containing_class == setup.Process
        assert len(context.parameters) == 0
        assert context.return_annotation == list
        assert context.typeInfo() == "static method of class Process"
