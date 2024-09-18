from .base_classmethod import BaseClassmethod, ModuleType, CoroutineDef, Parameter
from .custom_id import CustomID

class TestClassmethodCustomID(BaseClassmethod):

    SETUP_MODULE: str = "tests.setup_classmethod_custom_id"
    ALL_TARGETS: list[CustomID] = [CustomID(1, 'A'), CustomID(2, 'B'), CustomID(3, 'C'), CustomID(4, 'D')]

    def test_coroutine_def_info1(self, setup: ModuleType) -> None:
        ids = CoroutineDef.get_coroutine_ids()
        info = CoroutineDef.get_coroutine_def_info(ids[0])
        assert info.func.__qualname__ == setup.Process.ping.__qualname__
        assert info.func_name == self.COROUTINE_NAME
        assert info.module == self.SETUP_MODULE
        assert info.target_param == "id"

        coroutine_params = ["cls", "id", "msg", "sleep"]
        coroutine_param_types = [Parameter.empty, CustomID, str, int]

        context = info.context
        assert context.is_function == False
        assert context.is_method == False
        assert context.is_static_method == False
        assert context.is_class_method == True
        assert context.containing_class == setup.Process
        assert len(context.parameters) == len(coroutine_params)
        assert "self" not in context.parameters
        for p, t in zip(coroutine_params, coroutine_param_types):
            assert p in context.parameters
            assert context.parameters[p].annotation == t
        assert context.return_annotation == None
        assert context.typeInfo() == "class method of class Process"
