import asyncio

import aiohttp.web as web
import aiohttp_session
import aiohttp_jinja2

from .login import *
from .util import *

from .coroutine_def import CoroutineDef
from .coroutine_def_info import CoroutineDefInfo
from .task_exec import TaskExec
from .task_exec_info import TaskExecInfo
from .task_target_def import TaskTargetDef

from typing import Any

list_all_tasks : set[asyncio.Task] = set()

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

        # Get info about executing tasks and order them by target ID.
        all_exec_infos = TaskExec.get_all()
        all_exec_infos.sort(key=lambda ei: ei.target)

        task_display_info = []

        prev_target_pos = 0

        for exec_info in all_exec_infos:

            target = exec_info.target
            target_pos = self._task_targets.index(target, prev_target_pos)

            # Note: List of targets and list of tasks are sorted, hence the next task's
            # target must correspond to the current or a later entry in the list of targets.
            # Therefore, the position of the previous task's target is a good hint for finding
            # the position of the current task's target.
            prev_target_pos = target_pos

            # Get parameters of executing task. Remove 'self' from methods and 'cls' from class methods.
            params = exec_info.params.copy()
            if exec_info.coroutine_def.context.is_method: params.pop('self')
            if exec_info.coroutine_def.context.is_class_method: params.pop('cls')

            # Collect information about running task for display.
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

        # Return info for rendering Jinja template.
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

        # Retrieve target of executing task.
        target_pos = int(form['target-pos'])
        if target_pos >= len(self._task_targets): raise RuntimeError('Invalid target position')
        target = self._task_targets[target_pos]

        # Get info about executing task. Ignore type warnings, execution info is guaranteed to be available.
        exec_info : TaskExecInfo = TaskExec.get_by_id(str(form['task-id']), from_cache=True) # type: ignore[assignment]

        # Get parameters of executing task. Remove 'self' from methods and 'cls' from class methods.
        params = exec_info.params.copy()
        if exec_info.coroutine_def.context.is_method: params.pop('self')
        if exec_info.coroutine_def.context.is_class_method: params.pop('cls')

        # Return info for rendering Jinja template.
        return {
            'target': target,
            'target_pos': target_pos,
            'func_name': exec_info.coroutine_name,
            'module': exec_info.module,
            'params': params,
            'task_id': str(form['task-id']),
            'coroutine_id': str(form['coroutine-id']),
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

        # Retrieve target of executing task.
        target_pos = int(form['target-pos']) # type: ignore[arg-type]
        if target_pos >= len(self._task_targets): raise RuntimeError('Invalid target position')
        target = self._task_targets[target_pos]

        # Cancel running task.
        TaskExec.cancel(
            task_id=str(form['task-id']),
            coroutine_id=str(form['coroutine-id']),
            target=target,
        )

        # Go bask to index page.
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
        coroutine_id = str(form['coroutine-id'])

        # Retrieve target for new task.
        if target_pos >= len(self._task_targets): raise RuntimeError('Invalid target position')
        target = self._task_targets[target_pos]

        # Retrieve coroutine info for new task.
        def_info = CoroutineDef.get_coroutine_def_info(coroutine_id)
        if not def_info: raise RuntimeError('Unknown function ID')

        # Get code context of coroutine.
        context = def_info.context

        # Sanity check: Does the class containing the coroutine (if any)
        # match the process the dashboard is attached to?
        containing_class = context.containing_class
        if containing_class and not isinstance(self._process, containing_class):
            raise RuntimeError(
                f'Function "{def_info.func_name}" is not a method of class "{self._process.__class__.__name__}"'
            )

        # Retrieve params for new task. Remove target ID parameter (has already been selected before).
        params = context.parameters.copy()
        params.pop(def_info.target_param)

        if context.is_method or context.is_class_method:
            params.popitem(last=False) # Remove first parameter of method (self / cls).

        # Return info for rendering Jinja template.
        return {
            'coroutine_id': coroutine_id,
            'target_param': def_info.target_param,
            'target': target,
            'target_pos': target_pos,
            'params': params.values(),
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
        coroutine_id = str(form.pop('coroutine-id'))
        target_param = str(form.pop('target-param'))
        target_pos = int(form.pop('target-pos')) # type: ignore[arg-type]

        # Retrieve coroutine info. Ignore type warnings, coroutine info is guaranteed to be available.
        func_info: CoroutineDefInfo = CoroutineDef.get_coroutine_def_info(coroutine_id) # type: ignore[assignment]

        # Extract parameter names and their values for calling the coroutine.
        param_list = func_info.context.parameters
        param_apply = {
            k: param_list[k].default if not v else get_type_from_str(param_list[k],str(v)) for k, v in form.items()
        }

        # Retrieve target ID param value and add it to the parameters.
        if target_pos >= len(self._task_targets): raise RuntimeError('Invalid target position')
        target = self._task_targets[target_pos]
        param_apply[target_param] = target

        # Start new task.
        loop = asyncio.get_event_loop()
        if func_info.context.is_method:
            task = loop.create_task(func_info.func(self._process, **param_apply))
        else:
            task = loop.create_task(func_info.func(**param_apply))

        # Add to list of tasks, creating a strong reference to avoid the task disappearing mid-execution.
        list_all_tasks.add(task)
        # To prevent keeping references to finished tasks forever, make each task remove its own reference
        # from the set after completion.
        task.add_done_callback(list_all_tasks.discard)

        # Go bask to index page.
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
        password = str(form['password'])

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
