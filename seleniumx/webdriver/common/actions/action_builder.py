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

from seleniumx.webdriver.common.enums import Command
from seleniumx.webdriver.common.actions.interaction import InteractionType
from seleniumx.webdriver.common.actions.input_device import KeyInput, PointerInput

class ActionBuilder(object):
    
    def __init__(
        self,
        driver,
        mouse = None,
        keyboard = None
    ):
        if mouse is None:
            mouse = PointerInput(InteractionType.POINTER_MOUSE, "mouse")
        if keyboard is None:
            keyboard = KeyInput(InteractionType.KEY)
        self._devices = [mouse, keyboard]
        self._driver = driver
    
    @property
    def devices(self):
        return self._devices
    
    @property
    def pointer_inputs(self):
        return [device for device in self._devices if device.type == InteractionType.POINTER]

    @property
    def key_inputs(self):
        return [device for device in self._devices if device.type == InteractionType.KEY]

    @property
    def key_action(self):
        key_inputs = self.key_inputs
        if key_inputs:
            return key_inputs[0]

    @property
    def pointer_action(self):
        pointer_inputs = self.pointer_inputs
        if pointer_inputs:
            return pointer_inputs[0]
    
    def get_device_with_name(self, name):
        if not (self._devices and name):
            return None
        for device in self._devices:
            device_name = device.name
            if device_name.lower() == name.lower():
                return device

    def add_key_input(self, name):
        new_input = KeyInput(name)
        self._add_input(new_input)
        return new_input

    def add_pointer_input(self, kind, name):
        new_input = PointerInput(kind, name)
        self._add_input(new_input)
        return new_input

    async def perform(self):
        for device in self._devices:
            async for action_set in device.encode():
                if action_set and action_set.get('actions'):
                    await self._driver.execute(Command.W3C_ACTIONS, {'actions' : action_set})
            device.clear_actions()

    def clear_actions(self):
        """ Clears actions that are stored for each device """
        for device in self._devices:
            device.clear_actions()
    
    async def clear_remote_actions(self):
        """ Clears actions that are already stored on the remote end """
        await self._driver.execute(Command.W3C_CLEAR_ACTIONS)

    def _add_input(self, input_):
        self._devices.append(input_)
