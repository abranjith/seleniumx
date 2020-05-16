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

from seleniumx.webdriver.common.options import BaseOptions
from seleniumx.webdriver.common.desired_capabilities import DesiredCapabilities
from seleniumx.webdriver.chromium.webdriver import ChromiumDriver
from seleniumx.webdriver.edge.options import EdgeOptions
from seleniumx.webdriver.edge.service import EdgeService

class EdgeDriver(ChromiumDriver):
    """ Controls the Microsoft Edge driver and allows you to drive the browser.
    You will need to download either the MicrosoftWebDriver (Legacy)
    or MSEdgeDriver (Chromium) executable from
    https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
    """

    _VENDOR_PREFIX = "ms"
    DEFAULT_EXE = "MicrosoftWebDriver"
    DEFAULT_CHROMIUMBASED_EXE = "msedgedriver"

    def __init__(
        self, 
        executable_path : str = None,
        options : BaseOptions = None, 
        service_args = None,
        service_log_path = None,
        service = None, 
        keep_alive = False, 
        verbose = False,
        **kwargs
    ):
        """ Creates a new instance of the edge driver.
        Starts the service and then creates new instance of edge driver.

        :Args:
         - executable_path - Deprecated: path to the executable. If the default is used it assumes the executable is in the $PATH
         - options - this takes an instance of EdgeOptions
         - service_args - Deprecated: List of args to pass to the driver service
         - capabilities - Deprecated: Dictionary object with non-browser specific
           capabilities only, such as "proxy" or "loggingPref".
         - service_log_path - Deprecated: Where to log information from the driver.
         - keep_alive - Whether to configure EdgeRemoteConnection to use HTTP keep-alive.
         - verbose - whether to set verbose logging in the service.
         """

        executable_path = executable_path or EdgeDriver.DEFAULT_EXE
        options = options or self.create_options()
        if options is not None and options.use_chromium:
            executable_path = EdgeDriver.DEFAULT_CHROMIUMBASED_EXE
        if service is None:
            service = EdgeService(executable_path, service_args=service_args,
                                 log_path=service_log_path, verbose=verbose)
        browser_name = DesiredCapabilities.EDGE['browserName']
        super().__init__(browser_name, EdgeDriver._VENDOR_PREFIX, options=options, service_args=service_args,
                        service=service, keep_alive=keep_alive)

    def create_options(self):
        return EdgeOptions()
