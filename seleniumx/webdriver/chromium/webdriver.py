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

from seleniumx.webdriver.chromium.command_codec import ChromiumCommandCodec
from seleniumx.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from seleniumx.webdriver.common.enums import Command
from seleniumx.webdriver.common.options import BaseOptions
from seleniumx.webdriver.common.service import Service

class ChromiumDriver(RemoteWebDriver):
    """ Controls the WebDriver instance of ChromiumDriver and allows you to drive the browser. """

    def __init__(
        self,
        browser_name : str,
        vendor_prefix : str,
        options : BaseOptions = None,
        service_args : list = None, 
        service : Service = None,
        keep_alive : bool = True,
        **kwargs
    ):
        """ Creates a new WebDriver instance of the ChromiumDriver.
        Starts the service and then creates new WebDriver instance of ChromiumDriver.

        :Args:
            - browser_name - Browser name used when matching capabilities.
            - vendor_prefix - Company prefix to apply to vendor-specific WebDriver extension commands.
            - options - this takes an instance of ChromiumOptions
            - service_args - Deprecated: List of args to pass to the driver service
            - service  - A valid Service class that takes care of starting WebDriver service
            - keep_alive - Whether to configure ChromiumRemoteConnection to use HTTP keep-alive.
        """
        if service is None:
            raise AttributeError("WebDriver requires corresponding driver service to be provided")

        self.service = service
        command_codec = ChromiumCommandCodec(browser_name=browser_name, vendor_prefix=vendor_prefix)
        super().__init__(command_codec=command_codec, options=options, keep_alive=keep_alive, **kwargs)
        self._is_remote = False
    
    async def start_service(self):
        await self.service.start()
        self.server_url = self.service.service_url

    async def launch_app(self, id_):
        """ Launches Chromium app specified by id """
        await self.execute(Command.LAUNCH_APP, {'id': id_})

    async def get_network_conditions(self):
        """ Gets Chromium network emulation settings.

        :Returns:
            A dict. For example:
            {'latency': 4, 'download_throughput': 2, 'upload_throughput': 2,
            'offline': False}
        """
        response = await self.execute(Command.GET_NETWORK_CONDITIONS)
        return response['value']

    async def set_network_conditions(self, **network_conditions):
        """ Sets Chromium network emulation settings.

        :Args:
         - network_conditions: A dict with conditions specification.

        :Usage:
            ::

                driver.set_network_conditions(
                    offline=False,
                    latency=5,  # additional latency (ms)
                    download_throughput=500 * 1024,  # maximal throughput
                    upload_throughput=500 * 1024)  # maximal throughput

            Note: 'throughput' can be used to set both (for download and upload).
        """
        await self.execute(Command.SET_NETWORK_CONDITIONS, {'network_conditions': network_conditions})

    async def execute_cdp_cmd(self, cmd, cmd_args):
        """ Execute Chrome Devtools Protocol command and get returned result
        The command and command args should follow chrome devtools protocol domains/commands, refer to link
        https://chromedevtools.github.io/devtools-protocol/

        :Args:
         - cmd: A str, command name
         - cmd_args: A dict, command args. empty dict {} if there is no command args
        :Usage:
            ::
                driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': requestId})
        :Returns:
            A dict, empty dict {} if there is no result to return.
            For example to getResponseBody:
            {'base64Encoded': False, 'body': 'response body string'}
        """
        response = await self.execute(Command.EXECUTE_CDP_COMMAND, {'cmd': cmd, 'params': cmd_args})
        return response['value']

    async def get_sinks(self):
        """ :Returns: A list of sinks avaliable for Cast. """
        response = await self.execute(Command.GET_SINKS)
        return response['value']

    async def get_issue_message(self):
        """ :Returns: An error message when there is any issue in a Cast session. """
        response = await self.execute(Command.GET_ISSUE_MESSAGE)
        return response['value']

    async def set_sink_to_use(self, sink_name):
        """ Sets a specific sink, using its name, as a Cast session receiver target.

        :Args:
         - sink_name: Name of the sink to use as the target.
        """
        await self.execute(Command.SET_SINK_TO_USE, {'sinkName': sink_name})

    async def start_tab_mirroring(self, sink_name):
        """ Starts a tab mirroring session on a specific receiver target.

        :Args:
         - sink_name: Name of the sink to use as the target.
        """
        await self.execute(Command.START_TAB_MIRRORING, {'sinkName': sink_name})

    async def stop_casting(self, sink_name):
        """ Stops the existing Cast session on a specific receiver target.

        :Args:
         - sink_name: Name of the sink to stop the Cast session.
        """
        await self.execute(Command.STOP_CASTING, {'sinkName': sink_name})

    async def quit(self):
        """ Closes the browser and shuts down the ChromiumDriver executable
        that is started when starting the ChromiumDriver
        """
        try:
            await super().quit()
        except Exception:
            # We don't care about the message because something probably has gone wrong
            pass
        finally:
            await self.service.stop()
