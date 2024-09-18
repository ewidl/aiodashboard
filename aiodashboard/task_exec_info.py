from __future__ import annotations

from typing import Any
from dataclasses import dataclass
from collections import OrderedDict
from lazy import lazy

from .coroutine_def import CoroutineDef
from .coroutine_def_info import CoroutineDefInfo
from .util import coroutine_id

@dataclass
class TaskExecInfo:
    """
    Provide information about an executing task.
    """
    task_id: str
    coroutine_name: str
    module: str
    params: OrderedDict[str, Any]

    @property
    def coroutine_id(self) -> str:
        return coroutine_id(self.coroutine_name, self.module)

    @lazy
    def coroutine_def(self) -> CoroutineDefInfo:
        return CoroutineDef.get_coroutine_def_info(self.coroutine_id)

    @lazy
    def target(self) -> Any:
        return self.params[self.coroutine_def.target_param]
