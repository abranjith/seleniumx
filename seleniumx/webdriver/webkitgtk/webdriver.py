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

from seleniumx.webdriver.remote.webdriver import RemoteWebDriver
from seleniumx.webdriver.webkitgtk.service import WebKitGtkDriverService
from seleniumx.webdriver.webkitgtk.options import WebKitGtkOptions
from seleniumx.webdriver.common.options import BaseOptions

# TODO
# desired_capabilities is required ?
class WebKitGtkDriver(RemoteWebDriver):
    """ Controls the WebKitGTKDriver and allows you to drive the browser. """

    DEFAULT_EXE = "WebKitWebDriver"

    def __init__(
        self,
        executable_path : str = None,
        port : int = 0,
        options : BaseOptions = None,
        desired_capabilities = None,
        service_log_path = None,
        keep_alive = False,
        **kwargs
    ):
        """
        Creates a new instance of the WebKitGTK driver.

        Starts the service and then creates new instance of WebKitGTK Driver.

        :Args:
         - executable_path : path to the executable. If the default is used it assumes the executable is in the $PATH.
         - port : port you would like the service to run, if left as 0, a free port will be found.
         - options : an instance of WebKitGTKOptions
         - desired_capabilities : Dictionary object with desired capabilities
         - service_log_path : Path to write service stdout and stderr output.
         - keep_alive : Whether to configure RemoteConnection to use HTTP keep-alive.
        """
        desired_capabilities = desired_capabilities or {}
        if options:
            desired_capabilities.update(options.to_capabilities())

        self.service = WebKitGtkDriverService(executable_path, port=port, log_path=service_log_path)

        super().__init__(desired_capabilities=desired_capabilities, keep_alive=keep_alive, **kwargs)
        self._is_remote = False
    
    async def start_service(self):
        await self.service.start()
        self.server_url = self.service.service_url
    
    async def quit(self):
        """ Closes the browser and shuts down the WebKitGTKDriver executable
        that was started when starting the WebKitGTKDriver
        """
        try:
            await super().quit()
        except Exception as ex:
            warnings.warn(f"Something went wrong issuing quit request to server. Details - {str(ex)}")
        finally:
            await self.service.stop()
