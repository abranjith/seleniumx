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
from seleniumx.webdriver.ie.service import IEDriverService
from seleniumx.webdriver.ie.options import IEOptions

class IEDriver(RemoteWebDriver):
    """ Controls the IEServerDriver and allows you to drive Internet Explorer """

    _VENDOR_PREFIX = "goog"
    DEFAULT_EXE = "IEDriverServer.exe"

    def __init__(
        self,
        executable_path = None,
        host = None,
        log_level = None,
        service_log_path = None,
        options = None,
        service = None,
        keep_alive = False,
        **kwargs
    ):
        """ Creates a new instance of the Ie driver.

        Starts the service and then creates new instance of Ie driver.

        :Args:
         - executable_path - Deprecated: path to the executable. If the default is used it assumes the executable is in the $PATH
         - port - Deprecated: port you would like the service to run, if left as 0, a free port will be found.
         - timeout - Deprecated: no longer used, kept for backward compatibility
         - host - Deprecated: IP address for the service
         - log_level - Deprecated: log level you would like the service to run.
         - service_log_path - Deprecated: target of logging of service, may be "stdout", "stderr" or file path.
         - options - IE Options instance, providing additional IE options
         - desired_capabilities - Deprecated: alias of capabilities; this will make the signature consistent with RemoteWebDriver.
         - keep_alive - Whether to configure RemoteConnection to use HTTP keep-alive.
        """
        executable_path = executable_path or IEDriver.DEFAULT_EXE
        self.host = host
        options = options or self.create_options()
        self.service = service
        if self.service is None:
            self.service = IEDriverService(executable_path, host=self.host, log_level=log_level,
                                log_file=service_log_path)

        super().__init__(options=options, keep_alive=keep_alive, **kwargs)
        self._is_remote = False
    
    async def start_service(self):
        await self.service.start()
        self.server_url = self.service.service_url

    async def quit(self):
        """ Closes the browser and shuts down the IEDriverServer executable
        that was started when starting the IEDriverServer
        """
        try:
            await super().quit()
        except Exception as ex:
            warnings.warn(f"Something went wrong issuing quit request to server. Details - {str(ex)}")
        finally:
            await self.service.stop()

    def create_options(self):
        return IEOptions()
