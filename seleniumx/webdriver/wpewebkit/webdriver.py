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
from seleniumx.webdriver.wpewebkit.service import WPEWebKitDriverService
from seleniumx.webdriver.common.options import BaseOptions


class WPEWebKitDriver(RemoteWebDriver):
    """ Controls the WPEWebKitDriver and allows you to drive the browser. """
    
    DEFAULT_EXE = "WPEWebDriver"
    
    def __init__(
        self,
        executable_path : str= None,
        port : int = 0,
        options : BaseOptions = None,
        service_log_path = None,
        **kwargs
    ):
        """
        Creates a new instance of the WPEWebKit driver.

        Starts the service and then creates new instance of WPEWebKit Driver.

        :Args:
         - executable_path : path to the executable. If the default is used it assumes the executable is in the $PATH.
         - port : port you would like the service to run, if left as 0, a free port will be found.
         - options : an instance of WPEWebKitOptions
         - desired_capabilities : Dictionary object with desired capabilities
         - service_log_path : Path to write service stdout and stderr output.
        """

        executable_path = executable_path or WPEWebKitDriver.DEFAULT_EXE
        self.service = WPEWebKitDriverService(executable_path, port=port, log_path=service_log_path)
        super().__init__(options=options, **kwargs)
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

