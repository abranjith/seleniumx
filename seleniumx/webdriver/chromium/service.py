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

from seleniumx.webdriver.common.service import Service

class ChromiumService(Service):
    """ Object that manages the starting and stopping the WebDriver instance of the ChromiumDriver """

    def __init__(
        self,
        executable_path : str,
        port : int = 0,
        service_args : list = None,
        log_path : str = None,
        env : dict = None,
        start_error_message : str = None
    ):
        """ Creates a new instance of the Service

        :Args:
         - executable_path : Path to the WebDriver executable
         - port : Port the service is running on
         - service_args : List of args to pass to the WebDriver service
         - log_path : Path for the WebDriver service to log to
        """
        self.service_args = service_args or []
        if log_path:
            self.service_args.append(f"--log-path={log_path}")
        if start_error_message is None:
            raise AttributeError("start_error_message should not be empty")
        super().__init__(executable_path, port=port, env=env, start_error_message=start_error_message)

    def command_line_args(self):
        return [f"--port={self.port}"] + self.service_args
