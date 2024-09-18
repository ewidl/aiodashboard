from .base_staticmethod import BaseStaticmethod, CoroutineDef, ModuleType

class TestStaticmethod(BaseStaticmethod):

    SETUP_MODULE: str = "tests.setup_staticmethod"
    ALL_TARGETS: list[str] = ["IJK", "LMN"]

    def test_coroutine_def_info(self, setup: ModuleType) -> None:
        ids = CoroutineDef.get_coroutine_ids()
        info = CoroutineDef.get_coroutine_def_info(ids[0])
        assert info.func == setup.Process.ping
        assert info.func_name == self.COROUTINE_NAME
        assert info.module == self.SETUP_MODULE
        assert info.target_param == "id"

        coroutine_params = ["id", "msg", "sleep"]
        coroutine_param_types = [str, str, int]

        context = info.context
        assert context.is_function == False
        assert context.is_method == False
        assert context.is_static_method == True
        assert context.is_class_method == False
        assert context.containing_class == setup.Process
        assert len(context.parameters) == len(coroutine_params)
        assert "self" not in context.parameters
        for p, t in zip(coroutine_params, coroutine_param_types):
            assert p in context.parameters
            assert context.parameters[p].annotation == t
        assert context.return_annotation == None
        assert context.typeInfo() == "static method of class Process"
