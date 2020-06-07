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

import os
import base64

import aiofiles
from async_property import async_property

from seleniumx.webdriver.common.desired_capabilities import DesiredCapabilities
from seleniumx.webdriver.common.options import ArgOptions

class ChromiumOptions(ArgOptions):
    
    KEY = "goog:chromeOptions"
    LOAD_STRATEGY = ["normal", "eager", "none"] 

    def __init__(self):
        super().__init__()
        self._binary_location = ""
        self._extension_files = []
        self._extensions = []
        self._experimental_options = {}
        self._debugger_address = None

    @property
    def binary_location(self):
        """ :Returns: The location of the binary, otherwise an empty string """
        return self._binary_location

    @binary_location.setter
    def binary_location(
        self,
        value
    ):
        """ Allows you to set where the chromium binary lives
        :Args:
         - value: path to the Chromium binary
        """
        self._binary_location = value

    @property
    def debugger_address(self):
        """ :Returns: The address of the remote devtools instance """
        return self._debugger_address

    @debugger_address.setter
    def debugger_address(
        self,
        value
    ):
        """ Allows you to set the address of the remote devtools instance
        that the ChromeDriver instance will try to connect to during an
        active wait.
        :Args:
         - value: address of remote devtools instance if any (hostname[:port])
        """
        self._debugger_address = value

    @async_property
    async def extensions(self):
        """ :Returns: A list of encoded extensions that will be loaded """
        encoded_extensions = []
        for ext in self._extension_files:
            # Should not use base64.encodestring() which inserts newlines every
            # 76 characters (per RFC 1521).  Chromedriver has to remove those
            # unnecessary newlines before decoding, causing performance hit.
            async with aiofiles.open(ext, "rb") as fd:
                content = await fd.read()
                encoded_str = base64.b64encode(content).decode("UTF-8")
                encoded_extensions.append(encoded_str)
        return encoded_extensions + self._extensions

    def add_extension(
        self,
        extension
    ):
        """ Adds the path to the extension to a list that will be used to extract it
        to the ChromeDriver

        :Args:
         - extension: path to the \\*.crx file
        """
        if not extension:
            raise ValueError("extension is a required parameter")
        
        extension_to_add = os.path.abspath(os.path.expanduser(extension))
        if os.path.exists(extension_to_add):
            self._extension_files.append(extension_to_add)
        else:
            raise IOError(f"Path {extension_to_add} to the extension doesn't exist")

    def add_encoded_extension(
        self,
        extension
    ):
        """ Adds Base64 encoded string with extension data to a list that will be used to extract it
        to the ChromeDriver

        :Args:
         - extension: Base64 encoded string with extension data
        """
        if not extension:
            raise ValueError("extension is a required parameter")
        self._extensions.append(extension)

    @property
    def experimental_options(self):
        """ :Returns: A dictionary of experimental options for chromium """
        return self._experimental_options

    def add_experimental_option(
        self,
        name,
        value
    ):
        """ Adds an experimental option which is passed to chromium.

        :Args:
          name: The experimental option name.
          value: The option value.
        """
        self._experimental_options[name] = value

    @property
    def headless(self):
        """ :Returns: True if the headless argument is set, else False """
        return "--headless" in self._arguments

    @headless.setter
    def headless(
        self,
        value
    ):
        """ Sets the headless argument
        :Args:
          value: boolean value indicating to set the headless option
        """
        args = {"--headless"}
        if value is True:
            self._arguments.extend(args)
        else:
            self._arguments = list(set(self._arguments) - args)

    @property
    def page_load_strategy(self):
        return self._caps['pageLoadStrategy']

    @page_load_strategy.setter
    def page_load_strategy(
        self,
        strategy
    ):
        if strategy not in ChromiumOptions.LOAD_STRATEGY:
            raise ValueError(f"Strategy can only be one of the following: {', '.join(ChromiumOptions.LOAD_STRATEGY)}")
        self.set_capability("pageLoadStrategy", strategy)

    def to_capabilities(self):
        """ Creates a capabilities with all the options that have been set
        :Returns: A dictionary with everything
        """
        caps = self._caps
        chrome_options = self.experimental_options.copy()
        chrome_options['extensions'] = self.extensions
        chrome_options['args'] = self.arguments
        if self.binary_location:
            chrome_options['binary'] = self.binary_location
        if self.debugger_address:
            chrome_options['debuggerAddress'] = self.debugger_address
        caps[self.KEY] = chrome_options
        return caps

    @property
    def default_capabilities(self):
        return DesiredCapabilities.CHROME.copy()
