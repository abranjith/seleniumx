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

import base64
import shutil
import warnings
from contextlib import asynccontextmanager
import aiofiles

from seleniumx.webdriver.common.desired_capabilities import DesiredCapabilities
from seleniumx.webdriver.remote.webdriver import RemoteWebDriver
from seleniumx.webdriver.firefox.firefox_binary import FirefoxBinary
from seleniumx.webdriver.firefox.firefox_profile import FirefoxProfile
from seleniumx.webdriver.firefox.options import FirefoxOptions
from seleniumx.webdriver.firefox.service import FirefoxDriverService
from seleniumx.webdriver.firefox.command_codec import FirefoxCommandCodec
from seleniumx.webdriver.firefox.webelement import FirefoxWebElement
from seleniumx.webdriver.common.enums import Command
from seleniumx.webdriver.common.options import BaseOptions
from seleniumx.webdriver.common.service import Service

class FirefoxDriver(RemoteWebDriver):

    CONTEXT_CHROME = "chrome"
    CONTEXT_CONTENT = "content"
    DEFAULT_EXE = "geckodriver"
    DEFAULT_SERVICE_LOG_PATH = "geckodriver.log"

    _web_element_cls = FirefoxWebElement

    def __init__(
        self,
        timeout : int = 30,
        proxy = None,
        executable_path : str = None,
        options : BaseOptions = None,
        service_log_path : str = None,
        service_args : list = None,
        service : Service = None,
        keep_alive : bool = True,
        **kwargs
    ):
        """Starts a new local session of Firefox.

        Based on the combination and specificity of the various keyword
        arguments, a capabilities dictionary will be constructed that
        is passed to the remote end.

        The keyword arguments given to this constructor are helpers to
        more easily allow Firefox WebDriver sessions to be customised
        with different options.  They are mapped on to a capabilities
        dictionary that is passed on to the remote end.

        As some of the options, such as `firefox_profile` and
        `options.profile` are mutually exclusive, precedence is
        given from how specific the setting is.  `capabilities` is the
        least specific keyword argument, followed by `options`,
        followed by `firefox_binary` and `firefox_profile`.

        In practice this means that if `firefox_profile` and
        `options.profile` are both set, the selected profile
        instance will always come from the most specific variable.
        In this case that would be `firefox_profile`.  This will result in
        `options.profile` to be ignored because it is considered
        a less specific setting than the top-level `firefox_profile`
        keyword argument.  Similarly, if you had specified a
        `capabilities["moz:firefoxOptions"]["profile"]` Base64 string,
        this would rank below `options.profile`.

        :param firefox_profile: Instance of ``FirefoxProfile`` object
            or a string.  If undefined, a fresh profile will be created
            in a temporary location on the system.
        :param firefox_binary: Instance of ``FirefoxBinary`` or full
            path to the Firefox binary.  If undefined, the system default
            Firefox installation will  be used.
        :param timeout: Time to wait for Firefox to launch when using
            the extension connection.
        :param capabilities: Dictionary of desired capabilities.
        :param proxy: The proxy settings to use when communicating with
            Firefox via the extension connection.
        :param executable_path: Full path to override which geckodriver
            binary to use for Firefox 47.0.1 and greater, which
            defaults to picking up the binary from the system path.
        :param options: Instance of ``options.Options``.
        :param service_log_path: Where to log information from the driver.
        :param service_args: List of args to pass to the driver service
        :param desired_capabilities: alias of capabilities. In future
            versions of this library, this will replace 'capabilities'.
            This will make the signature consistent with RemoteWebDriver.
        :param keep_alive: Whether to configure remote_connection.RemoteConnection to use
             HTTP keep-alive.
        """

        executable_path = executable_path or FirefoxDriver.DEFAULT_EXE
        self.binary = None
        self.profile = None
        if service is None:
            service = FirefoxDriverService(executable_path, service_args=service_args, log_path=service_log_path)
        self.service = service
        if options is None:
            options = FirefoxOptions()
        if options.binary is not None:
            self.binary = options.binary
        if options.profile is not None:
            self.profile = options.profile

        browser_name = DesiredCapabilities.FIREFOX['browserName']
        command_codec = FirefoxCommandCodec(browser_name=browser_name)
        super().__init__(command_codec=command_codec, options=options, keep_alive=keep_alive, **kwargs)
        self._is_remote = False
    
    async def start_service(self):
        await self.service.start()
        self.server_url = self.service.service_url
    
    async def quit(self):
        """ Closes the browser and shuts down the Driver executable that was started when starting the Driver """
        try:
            await super().quit()
        except Exception as ex:
            warnings.warn(f"Something went wrong issuing quit request to server. Details - {str(ex)}")
        finally:
            if self.w3c:
                await self.service.stop()
            else:
                if self.binary:
                    self.binary.kill()
            if self.profile is not None:
                try:
                    shutil.rmtree(self.profile.path)
                    if self.profile and self.profile.tempfolder is not None:
                        shutil.rmtree(self.profile.tempfolder)
                except Exception as ex:
                    warnings.warn(f"Exception cleaning up Firefox profile. Details - {str(ex)}")

    @property
    def firefox_profile(self):
        return self.profile

    # Extension commands:
    async def set_context(self, context):
        await self.execute(Command.SET_CONTEXT, {'context': context})

    @asynccontextmanager
    async def context(self, context):
        """Sets the context that Selenium commands are running in using
        a `with` statement. The state of the context on the server is
        saved before entering the block, and restored upon exiting it.

        :param context: Context, may be one of the class properties
            `CONTEXT_CHROME` or `CONTEXT_CONTENT`.

        Usage example::

            with selenium.context(selenium.CONTEXT_CHROME):
                # chrome scope
                ... do stuff ...
        """
        response = await self.execute(Command.GET_CONTEXT)
        initial_context = response.get('value')
        await self.set_context(context)
        try:
            yield
        finally:
            await self.set_context(initial_context)

    async def install_addon(self, path, temporary=None):
        """
        Installs Firefox addon.

        Returns identifier of installed addon. This identifier can later
        be used to uninstall addon.

        :param path: Absolute path to the addon that will be installed.

        :Usage:
            ::

                driver.install_addon('/path/to/firebug.xpi')
        """
        payload = {'path': path}
        if temporary is not None:
            payload['temporary'] = temporary
        response = await self.execute(Command.INSTALL_ADDON, payload)
        return response['value']

    async def uninstall_addon(self, identifier):
        """
        Uninstalls Firefox addon using its identifier.

        :Usage:
            ::

                driver.uninstall_addon('addon@foo.com')
        """
        await self.execute(Command.UNINSTALL_ADDON, {'id': identifier})

    async def get_full_page_screenshot_as_file(self, filename):
        """
        Saves a full document screenshot of the current window to a PNG image file. Returns
           False if there is any IOError, else returns True. Use full paths in
           your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to. This
           should end with a `.png` extension.

        :Usage:
            ::

                driver.get_full_page_screenshot_as_file('/Screenshots/foo.png')
        """
        if not filename.lower().endswith('.png'):
            warnings.warn("name used for saved screenshot does not match file "
                          "type. It should end with a `.png` extension", UserWarning)

        png_file = await self.get_full_page_screenshot_as_png()
        try:
            async with aiofiles.open(filename, mode="wb") as fd:
                await fd.write(png_file)
        except IOError:
            return False
        finally:
            del png_file
        return True

    async def save_full_page_screenshot(self, filename):
        """
        Saves a full document screenshot of the current window to a PNG image file. Returns
           False if there is any IOError, else returns True. Use full paths in
           your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to. This
           should end with a `.png` extension.

        :Usage:
            ::

                driver.save_full_page_screenshot('/Screenshots/foo.png')
        """
        return await self.get_full_page_screenshot_as_file(filename)

    async def get_full_page_screenshot_as_png(self):
        """
        Gets the full document screenshot of the current window as a binary data.

        :Usage:
            ::

                driver.get_full_page_screenshot_as_png()
        """
        base64_screenshot = await self.get_full_page_screenshot_as_base64().encode("ascii")
        return base64.b64decode(base64_screenshot)

    async def get_full_page_screenshot_as_base64(self):
        """
        Gets the full document screenshot of the current window as a base64 encoded string
           which is useful in embedded images in HTML.

        :Usage:
            ::

                driver.get_full_page_screenshot_as_base64()
        """
        response = await self.execute(Command.FULL_PAGE_SCREENSHOT)
        return response['value']
