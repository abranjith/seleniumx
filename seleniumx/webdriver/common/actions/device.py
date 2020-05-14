# Licensed to the Software Freedom Conservancy (SFC) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The SFC licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import uuid
import inspect
from collections import namedtuple
from async_property import async_property

class Device(object):
    """ Describes the input device being used for the action. """
    def __init__(
        self,
        name = None
    ):
        self.name = name if name is not None else uuid.uuid4()
    
    #default impl. Note that this methid is supposed to be an async_generator (usable in async for)
    async def encode(self):
        yield

class InputDevice(Device):
    """ Describes the input device being used for the action. """
    def __init__(
        self,
        name = None
    ):
        super().__init__(name)
        self._actions = []
    
    @property
    def all_actions(self):
        return self._actions
    
    async def iter_actions(self):
        #sends actions in groups of that dont have pre-actions
        ready_actions = []
        for action in self._actions:
            if not action.has_pre_actions:
                ready_action = await action.action()
                ready_actions.append(ready_action)
            else:
                if ready_actions:
                    yield ready_actions 
                await action.perform_all_pre_actions()
                ready_action = await action.action()
                ready_actions[ready_action]
        #finally if there are any pending yield those actions as well
        if ready_actions:
            yield ready_actions 
    
    def add_action(self, action):
        if isinstance(action, dict):
            action = Action(action=action)
        self._actions.append(action)

    def clear_actions(self):
        self._actions = []
    
    def dispatch(self, action, add_to_action=True):
        if add_to_action:
            self.add_action(action)
        return action

#NOTE - not used currently
class OutputDevice(Device):
    pass


class Action(object):
    """ This class represents a particular action such as key down, move pointer etc. Unfortunately these operations are not
    atomic and this is an attempt to solve some of that.
    For eg - before moving to an element (action), get its co-ordinates from browser (pre-action) and use the return value as params
    to the action. So, there could be one or more such pre-actions that need to occur 
    This class also solves for more complex cases such as chaining of multiple pre-actions. With that, user can specify all the
    pre-actions (sync or async) that needs to happen in order where return value from previous action can be passed over to next and so on.
    Since python provides many ways of specifying arguments for a function, it is difficult to cater for all those cases. This class only
    solves for cases where return values from previous call matches next call (position wise). User needs to keep this in mind before desiging the
    functions. Any specific pre-action can be thought of as pre-action(args + previous_return_args). And results from final pre-action can be passed
    over to the action_fn
    WARNING - user is responsible for overall orchestration (that is perform pre actions before invoking final action  object). 
              If not results will not be accurate.
    """
        
    PreAction = namedtuple("PreAction", ["task", "args", "pass_from_previous_call"])
    ActionFn = PreAction
    
    def __init__(self, action=None):
        self._pre_actions = []
        #_action_fn(args) == action
        self._action_fn = None
        self._action = action
    
    @property
    def has_pre_actions(self):
        return len(self._pre_actions) > 0
    
    async def action(self):
        #_action and action_fn cannot co-exist
        if self._action is not None:
            return self._action
        if self._action_fn is not None:
            self._action = await self._fn_orchestrator(self._action_fn.task, self._action_fn.args)
        return self._action
    
    def add_pre_action(self, pre_action, args=None, pass_from_previous_call=True):
        pre_action = Action.PreAction(task=pre_action, args=args, pass_from_previous_call=pass_from_previous_call)
        self._pre_actions.append(pre_action)
    
    def add_action_fn(self, action_fn, args=None, pass_from_previous_call=True):
        self._action_fn = Action.ActionFn(task=action_fn, args=args, pass_from_previous_call=pass_from_previous_call)
    
    async def perform_all_pre_actions(self):
        if not self._pre_actions:
            return
        return_args = None
        for a in self._pre_actions:
            final_args = self._get_merged_args(a.args, a.pass_from_previous_call, return_args)
            return_args = await self._fn_orchestrator(a.task, final_args)
        #finalize args for actual action function call
        if self._action_fn is not None:
            final_args = self._get_merged_args(self._action_fn.args, self._action_fn.pass_from_previous_call, return_args)
            self._action_fn.args = final_args

    def _get_merged_args(self, args, pass_from_previous_call, previous_return_args):
        final_args = ()
        if self._get_args(args):
            final_args += args
        if pass_from_previous_call and previous_return_args:
            if isinstance(previous_return_args, tuple):
                final_args += previous_return_args
            else:
                final_args += (previous_return_args,)
        return final_args
    
    def _get_args(self, args):
        if args:
            if not isinstance(args, tuple):
                args = (args,)
        return args
    
    async def _fn_orchestrator(self, fn, args):
        return_args = None
        if inspect.iscoroutinefunction(fn):
            if args:
                return_args = await fn(*args)
            else:
                return_args = await fn()
        elif callable(fn):
            if args:
                return_args = fn(*args)
            else:
                return_args = fn()
        return return_args
