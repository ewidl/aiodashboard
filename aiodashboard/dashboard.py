import asyncio

import aiohttp.web as web
import aiohttp_session
import aiohttp_jinja2

from .login import *
from .util import *

from .coroutine_def import CoroutineDef
from .task_exec import TaskExec
from .task_target_def import TaskTargetDef

from typing import Any

all_tasks = set()

class Dashboard:

    def __init__(
            self,
            pwd_hash: bytes,
            process: Any = None,
            static_targets: bool = False
        ) -> None:
        """
        Contructor.
        """
        self._pwd_hash = PasswordHash(pwd_hash)
        self._process = process
        self._static_targets = static_targets

        # Sanity checks for task targets and task definitions. 
        TaskTargetDef.check()
        CoroutineDef.check()

        # In case the list of targets will not change during 
        # runtime, it can be retrieved now and remain constant.
        if True == self._static_targets: self._retrieve_target_list()

    @require_login
    @aiohttp_jinja2.template('index.html')
    async def index(
            self,
            request: web.Request
        ) -> dict[str, Any]:
        """
        Main content page.
        """
        # In case the list of targets may change during 
        # runtime, it needs to be retrieved every time.
        if False == self._static_targets: self._retrieve_target_list()

        all_exec_infos = TaskExec.get_all()
        all_exec_infos.sort(key=lambda ei: ei.target)

        task_display_info = []

        prev_target_pos = 0

        for exec_info in all_exec_infos:

            target = exec_info.target
            target_pos = self._task_targets.index(target, prev_target_pos)
            
            # Note: List of targets and list of tasks are sorted, hence the next task's 
            # target must correspond to the current or a later entry in the list of targets.
            # Therefore, the position of the current task's target is a good hint for finding
            # the position of the next task's target. 
            prev_target_pos = target_pos

            params = exec_info.params.copy()
            if exec_info.coroutine_def.context.is_method:
                params.pop('self')

            task_display_info.append((
                target,
                target_pos,
                exec_info.coroutine_name,
                exec_info.module,
                exec_info.task_id,
                exec_info.coroutine_id,
                params,
                exec_info.coroutine_def.context.typeInfo()
            ))

        return {
            'coroutine_defs': CoroutineDef.get_coroutine_defs(),
            'task_display_info': task_display_info, 
            'task_targets': self._task_targets,
        }

    @require_login
    @aiohttp_jinja2.template('cancel-task.html')
    async def cancel_task(
            self,
            request: web.Request
        ) -> dict[str, Any]:
        """
        Task cancellation page.
        """
        form = request.query

        target_pos = int(form['target-pos'])
        target = self._task_targets[target_pos]

        exec_info = TaskExec.get_by_id(form['task-id'], from_cache=True)

        params = exec_info.params.copy()
        if exec_info.coroutine_def.context.is_method:
            params.pop('self')

        return {
            'target': target,
            'target_pos': target_pos,
            'func_name': exec_info.coroutine_name,
            'module': exec_info.module,
            'params': params,
            'task_id': form['task-id'],
            'coroutine_id': form['coroutine-id'],
        }

    @require_login
    async def cancel_task_apply(
            self,
            request: web.Request
        ) -> web.Response:
        """
        Handle task cancellation.
        """
        form = await request.post()

        target_pos = int(form['target-pos'])
        target = self._task_targets[target_pos]

        TaskExec.cancel(
            task_id=form['task-id'], 
            coroutine_id=form['coroutine-id'],
            target=target,
        )
        raise web.HTTPSeeOther(location='/')

    @require_login
    @aiohttp_jinja2.template('start-task.html')
    async def start_task(
            self,
            request: web.Request
        ) -> dict[str, Any]:
        """
        Task start-up page.
        """
        form = request.query
        target_pos = int(form['target-pos'])
        coroutine_id = form['coroutine-id']

        if target_pos >= len(self._task_targets): raise RuntimeError('Invalid target position')
        target = self._task_targets[target_pos]

        def_info = CoroutineDef.get_coroutine_def_info(coroutine_id)
        if not def_info: raise RuntimeError('Unknown function ID')

        context = def_info.context

        containing_class = context.containing_class
        if containing_class and not isinstance(self._process, containing_class):
            raise RuntimeError(
                f'Function "{def_info.func_name}" is not a method of class "{self._process.__class__.__name__}"'
            )

        params = context.parameters.copy()
        params.pop(def_info.target_param)

        if context.is_method:
            params.popitem(last=False) # Remove first parameter of method (self). 

        return {
            'coroutine_id': coroutine_id, 
            'target_param': def_info.target_param, 
            'target': target, 
            'target_pos': target_pos, 
            'params': params.values(), 
            # 'no_default': inspect.Parameter.empty, 
            'get_type': get_html_input_type
        }

    @require_login
    async def start_task_apply(
            self,
            request: web.Request
        ) -> web.Response:
        """
        Handle task start-up.
        """
        form = (await request.post()).copy()
        coroutine_id = form.pop('coroutine-id')
        target_param = form.pop('target-param')
        target_pos = int(form.pop('target-pos'))

        func_info = CoroutineDef.get_coroutine_def_info(coroutine_id)
        param_list = func_info.context.parameters
        param_apply = {
            k: param_list[k].default if not v else get_type_from_str(param_list[k],v) for k, v in form.items()
        }

        if target_pos >= len(self._task_targets): raise RuntimeError('Invalid target position')
        target = self._task_targets[target_pos]
        param_apply[target_param] = target

        loop = asyncio.get_event_loop()
        if func_info.context.is_method:
            task = loop.create_task(func_info.func(self._process, **param_apply))
        else:
            task = loop.create_task(func_info.func(**param_apply))

        all_tasks.add(task)
        task.add_done_callback(all_tasks.discard)

        raise web.HTTPSeeOther(location='/')

    @aiohttp_jinja2.template('login.html')
    async def login(
            self,
            request: web.Request
        ) -> dict[str, Any]:
        """
        Login page.
        """
        # Retrieve session.
        session = await aiohttp_session.get_session(request)

        # Get login status.
        login_status = session.get('login_status', LoginStatus.LOGGED_OUT)

        # Display login page.
        if login_status == LoginStatus.FAILED:
            return {'info': 'Login failed.'}
        else:
            return {}

    async def login_apply(
            self,
            request: web.Request
        ) -> web.Response:
        """
        Handle login attempts.
        """
        # Retrieve session.
        session = await aiohttp_session.get_session(request)

        # Get entered password.
        form = await request.post()
        password = form['password']

        # Check entered password.
        if self._pwd_hash.check(password):
            # Correct password: redirect to main content page.
            session['login_status'] = LoginStatus.LOGGED_IN
            raise web.HTTPSeeOther(location='/')
        else:
            # Incorrect password: redirect to login page.
            session['login_status'] = LoginStatus.FAILED
            raise web.HTTPSeeOther(location='/login')

    async def logout(
            self,
            request: web.Request
        ) -> web.Response:
        """
        Handle logout.
        """
        # Retrieve session.
        session = await aiohttp_session.get_session(request)

        # Reset login status.
        session['login_status'] = LoginStatus.LOGGED_OUT

        # Redirect to login page.
        raise web.HTTPSeeOther(location="/login")

    def _retrieve_target_list(self) -> None:
        self._task_targets = TaskTargetDef.get_targets(process=self._process)
        self._task_targets.sort()
