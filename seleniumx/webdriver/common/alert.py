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

from async_property import async_property

from seleniumx.webdriver.common.enums import Command
from seleniumx.webdriver.common.utils import keys_to_typing
from seleniumx.webdriver.remote.command import CommandInfo

class Alert(object):
    """ Allows to work with alerts.

    Use this class to interact with alert prompts.  It contains methods for dismissing,
    accepting, inputting, and getting text from alert prompts.

    Accepting / Dismissing alert prompts::

        Alert(driver).accept()
        Alert(driver).dismiss()

    Inputting a value into an alert prompt:

        name_prompt = Alert(driver)
        name_prompt.send_keys("Willian Shakesphere")
        name_prompt.accept()


    Reading a the text of a prompt for verification:

        alert_text = Alert(driver).text
        self.assertEqual("Do you wish to quit?", alert_text)

    """

    def __init__(self, driver):
        """
        Creates a new Alert.

        :Args:
         - driver: The WebDriver instance which performs user actions.
        """
        self._driver = driver
        self._w3c = self._driver.w3c

    @async_property
    async def text(self):
        """ Gets the text of the Alert """
        command = Command.W3C_GET_ALERT_TEXT if self._w3c else Command.GET_ALERT_TEXT
        response = await self._driver.execute(command)
        return response['value']

    async def dismiss(self):
        """ Dismisses the alert available. """
        command = Command.W3C_DISMISS_ALERT if self._w3c else Command.DISMISS_ALERT
        await self._driver.execute(command)

    async def accept(self):
        """ Accepts the alert available.

        Usage::
        Alert(driver).accept() # Confirm a alert dialog.
        """
        command = Command.W3C_ACCEPT_ALERT if self._w3c else Command.ACCEPT_ALERT
        await self._driver.execute(command)

    async def send_keys(
        self,
        keys_to_send
    ):
        """ Send Keys to the Alert.

        :Args:
         - keys_to_send: The text to be sent to Alert.


        """
        if self._w3c:
            await self._driver.execute(Command.W3C_SET_ALERT_VALUE, {'value': keys_to_typing(keys_to_send),
                                                                    'text': keys_to_send})
        else:
            await self._driver.execute(Command.SET_ALERT_VALUE, {'text': keys_to_send})
