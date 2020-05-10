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

from seleniumx.webdriver.chromium.webdriver import ChromiumDriver
from seleniumx.webdriver.common.desired_capabilities import DesiredCapabilities
from seleniumx.webdriver.chrome.options import ChromeOptions
from seleniumx.webdriver.chrome.service import ChromeDriverService
from seleniumx.webdriver.common.service import Service
from seleniumx.webdriver.common.options import BaseOptions

class ChromeDriver(ChromiumDriver):
    """ Controls the ChromeDriver and allows you to drive the browser.
    You will need to download the ChromeDriver executable from
    http://chromedriver.storage.googleapis.com/index.html
    """
    _VENDOR_PREFIX = "goog"
    DEFAULT_EXE = "chromedriver"

    def __init__(
      self,
      executable_path : str = None,
      options : BaseOptions = None,
      service_args : list = None,
      service_log_path : str = None,
      service : Service = None,
      keep_alive : bool = True,
      **kwargs
    ):
        """ Creates a new instance of the chrome driver.
        Starts the service and then creates new instance of chrome driver.

        :Args:
         - options - this takes an instance of ChromeOptions
         - service_args - Deprecated: List of args to pass to the driver service
         - service_log_path - Where to log information from the driver.
         - service  - A valid Service class that takes care of starting WebDriver service
         - keep_alive - Whether to configure ChromeRemoteConnection to use HTTP keep-alive.
        """
        executable_path = executable_path or ChromeDriver.DEFAULT_EXE
        if service is None:
            service = ChromeDriverService(executable_path, service_args=service_args,
                                          log_path=service_log_path)
        options = options or self.create_options()
        browser_name = DesiredCapabilities.CHROME['browserName']
        super().__init__(browser_name, ChromeDriver._VENDOR_PREFIX, options=options, service_args=service_args,
                        service=service, keep_alive=keep_alive)

    def create_options(self):
        return ChromeOptions()
