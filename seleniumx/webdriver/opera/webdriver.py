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
from seleniumx.webdriver.chrome.webdriver import ChromeDriver
from seleniumx.webdriver.opera.options import OperaOptions

class OperaDriver(ChromeDriver):
    """Controls the new OperaDriver and allows you
    to drive the Opera browser based on Chromium."""

    DEFAULT_EXE = "operadriver"

    def __init__(
        self,
        executable_path : str = None,
        options : BaseOptions = None,
        service_args : list = None,
        service_log_path : str = None,
        keep_alive : bool = True,
        **kwargs
    ):
        """
        Creates a new instance of the operadriver.

        Starts the service and then creates new instance of operadriver.

        :Args:
         - executable_path - path to the executable. If the default is used
                             it assumes the executable is in the $PATH
         - options: this takes an instance of OperaOptions
         - service_args - List of args to pass to the driver service
         - service_log_path - Where to log information from the driver.
           capabilities only, such as "proxy" or "loggingPref".
        """
        executable_path = executable_path or OperaDriver.DEFAULT_EXE
        super().__init__(executable_path=executable_path, options=options, service_args=service_args,
                        service_log_path=service_log_path, keep_alive=keep_alive)

    def create_options(self):
        return OperaOptions()
