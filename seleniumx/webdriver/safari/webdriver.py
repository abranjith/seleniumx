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

import warnings

from seleniumx.webdriver.common.enums import Command
from seleniumx.common.exceptions import WebDriverException
from seleniumx.webdriver.common.service import Service
from seleniumx.webdriver.common.desired_capabilities import DesiredCapabilities
from seleniumx.webdriver.remote.webdriver import RemoteWebDriver
from seleniumx.webdriver.safari.service import SafariDriverService
from seleniumx.webdriver.safari.command_codec import SafariCommandCodec

class SafariDriver(RemoteWebDriver):
    """ Controls the SafariDriver and allows you to drive the browser. """
    
    DEFAULT_EXE = "/usr/bin/safaridriver"

    def __init__(
        self,
        port = 0,
        executable_path = None, 
        service : Service = None,
        desired_capabilities = None,
        quiet = False,
        keep_alive = True,
        service_args = None,
        **kwargs    
    ):
        """ Creates a new Safari driver instance and launches or finds a running safaridriver service.

        :Args:
         - port - The port on which the safaridriver service should listen for new connections. If zero, a free port will be found.
         - executable_path - Path to a custom safaridriver executable to be used. If absent, /usr/bin/safaridriver is used.
         - reuse_service - If True, do not spawn a safaridriver instance; instead, connect to an already-running service that was launched externally.
         - desired_capabilities: Dictionary object with desired capabilities (Can be used to provide various Safari switches).
         - quiet - If True, the driver's stdout and stderr is suppressed.
         - keep_alive - Whether to configure SafariRemoteConnection to use
             HTTP keep-alive. Defaults to False.
         - service_args : List of args to pass to the safaridriver service
        """

        executable_path = executable_path or SafariDriver.DEFAULT_EXE
        desired_capabilities = DesiredCapabilities.SAFARI.copy()
        if service is None:
            service = SafariDriverService(executable_path, port=port, service_args=service_args, quiet=quiet)
        self.service = service
        browser_name = DesiredCapabilities.SAFARI['browserName']
        command_codec = SafariCommandCodec(browser_name)
        super().__init__(command_codec=command_codec, desired_capabilities=desired_capabilities, keep_alive=keep_alive, **kwargs)
        self._is_remote = False
    
    async def start_service(self):
        await self.service.start()
        self.server_url = self.service.service_url
    
    async def quit(self):
        """ Closes the browser and shuts down the Driver service
        """
        try:
            await super().quit()
        except Exception as ex:
            warnings.warn(f"Something went wrong issuing quit request to server. Details - {str(ex)}")
        finally:
            await self.service.stop()

    # safaridriver extension commands. The canonical command support matrix is here:
    # https://developer.apple.com/library/content/documentation/NetworkingInternetWeb/Conceptual/WebDriverEndpointDoc/Commands/Commands.html
    # First available in Safari 11.1 and Safari Technology Preview 41.
    async def set_permission(self, permission, value):
        if not isinstance(value, bool):
            raise WebDriverException("Value of a session permission must be set to True or False.")
        payload = {}
        payload[permission] = value
        await self.execute(Command.SET_PERMISSIONS, {'permissions': payload})

    # First available in Safari 11.1 and Safari Technology Preview 41.
    async def get_permission(self, permission):
        response = await self.execute(Command.GET_PERMISSIONS)
        response = response['value']
        permissions = response.get('permissions')
        if not (permissions and permission in permissions):
            return None
        value = permissions[permission]
        if not isinstance(value, bool):
            return None
        return value

    # First available in Safari 11.1 and Safari Technology Preview 42.
    async def debug(self):
        await self.execute(Command.ATTACH_DEBUGGER)
        await self.execute_script("debugger;")
