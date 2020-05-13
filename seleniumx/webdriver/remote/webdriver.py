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
import copy
import pkgutil
import warnings
import inspect
from contextlib import contextmanager

import aiofiles
from async_property import async_property

from seleniumx.common.exceptions import (InvalidArgumentException,
                                        WebDriverException,
                                        NoSuchCookieException,
                                        UnknownMethodException)
from seleniumx.webdriver.common.by import By
from seleniumx.webdriver.common.timeouts import Timeouts
from seleniumx.webdriver.common.enums import Command
from seleniumx.webdriver.support.relative_locator import RelativeBy
from seleniumx.webdriver.remote.command_codec import CommandCodec
from seleniumx.webdriver.remote.http_executor import HttpExecutor
from seleniumx.webdriver.remote.errorhandler import ErrorHandler
from seleniumx.webdriver.remote.file_detector import FileDetector, LocalFileDetector
from seleniumx.webdriver.remote.mobile import Mobile
from seleniumx.webdriver.remote.switch_to import SwitchTo
from seleniumx.webdriver.remote.webelement import WebElement


_W3C_CAPABILITY_NAMES = frozenset([
    'acceptInsecureCerts',
    'browserName',
    'browserVersion',
    'platformName',
    'pageLoadStrategy',
    'proxy',
    'setWindowRect',
    'timeouts',
    'unhandledPromptBehavior',
    'strictFileInteractability'
])

_OSS_W3C_CONVERSION = {
    'acceptSslCerts': "acceptInsecureCerts",
    'version': "browserVersion",
    'platform': "platformName"
}

class _BaseDriver(object):
    """ Moved some non driver specific code here """

    def __init__(
        self,
        file_detector = None
    ):
        self.file_detector = file_detector or LocalFileDetector()

    @property
    def file_detector(self):
        return self._file_detector

    @file_detector.setter
    def file_detector(self, detector):
        """
        Set the file detector to be used when sending keyboard input.
        By default, this is set to a file detector that does nothing.

        see FileDetector
        see LocalFileDetector
        see UselessFileDetector

        :Args:
         - detector: The detector to use. Must not be None.
        """
        if detector is None:
            raise WebDriverException("You may not set a file detector that is null")
        if not isinstance(detector, FileDetector):
            raise WebDriverException("Detector has to be instance of FileDetector")
        self._file_detector = detector
    
    @contextmanager
    def file_detector_context(self, file_detector_class, *args, **kwargs):
        """ Overrides the current file detector (if necessary) in limited context.
        Ensures the original file detector is set afterwards.

        Example:

        with webdriver.file_detector_context(FileDetector):
            someinput.send_keys('/etc/hosts')

        :Args:
         - file_detector_class - Class of the desired file detector. If the class is different
             from the current file_detector, then the class is instantiated with args and kwargs
             and used as a file detector during the duration of the context manager.
         - args - Optional arguments that get passed to the file detector class during
             instantiation.
         - kwargs - Keyword arguments, passed the same way as args.
        """
        last_detector = None
        if not isinstance(self.file_detector, file_detector_class):
            last_detector = self.file_detector
            self.file_detector = file_detector_class(*args, **kwargs)
        try:
            yield
        finally:
            if last_detector is not None:
                self.file_detector = last_detector
    
    def start_service(self):
        """ Called before starting a new session. This method may be overridden by specific WebDriver implementation """
        pass
    
    def start_client(self):
        """
        Called before starting a new session. This method may be overridden
        to define custom startup behavior.
        """
        pass

    def stop_client(self):
        """
        Called after executing a quit command. This method may be overridden
        to define custom shutdown behavior.
        """
        pass
       
    def _make_w3c_capabilities(self, capabilities):
        """ Makes a W3C always match capabilities object.

        Filters out capability names that are not in the W3C spec. Spec-compliant
        drivers will reject requests containing unknown capability names.

        Moves the Firefox profile, if present, from the old location to the new Firefox
        options object.

        :Args:
        - capabilities - A dictionary of capabilities requested by the caller.
        """
        capabilities = copy.deepcopy(capabilities)
        always_match = {}
        #make lower case
        if capabilities.get('proxy') and capabilities['proxy'].get('proxyType'):
            capabilities['proxy']['proxyType'] = capabilities['proxy']['proxyType'].lower()
        for k, v in capabilities.items():
            #change name per w3c convention
            if v and (k in _OSS_W3C_CONVERSION):
                always_match[_OSS_W3C_CONVERSION[k]] = v.lower() if k == "platform" else v
            #only pull valid capabilities
            if (k in _W3C_CAPABILITY_NAMES) or ":" in k:
                always_match[k] = v
        
        #TODO - this should probably be under firefox driver. Special handling for firefox (setting profile)
        profile = capabilities.get('firefox_profile')
        if profile:
            moz_opts = always_match.get('moz:firefoxOptions', {})
            # If it's already present, assume the caller did that intentionally.
            if "profile" not in moz_opts:
                # Don't mutate the original capabilities.
                new_opts = copy.deepcopy(moz_opts)
                new_opts['profile'] = profile
                always_match['moz:firefoxOptions'] = new_opts
        return {"firstMatch": [{}], "alwaysMatch": always_match}
    
    #TODO - once CommandCodec is available for all browsers, update logic 
    def _determine_command_codec(self, capabilities):
        all_codecs = [CommandCodec]
        browser_name = capabilities.get('browserName')
        if not browser_name:
            return CommandCodec()
        browser_name = browser_name.strip().lower()
        for codec in all_codecs:
            if hasattr(codec, 'browser_name'):
                codec_browser_name = codec.browser_name
                if not codec_browser_name:
                    continue
                codec_browser_name = codec_browser_name.strip().lower()
                if codec_browser_name == browser_name:
                    return codec()
        return CommandCodec()
    
    
class RemoteWebDriver(_BaseDriver):
    """ Controls a browser by sending commands to a remote server.
    This server is expected to be running the WebDriver wire protocol
    as defined at
    https://w3c.github.io/webdriver/#algorithms

    :Attributes:
     - session_id - String ID of the browser session started and controlled by this WebDriver.
     - capabilities - Dictionary of effective capabilities of this browser session as returned
         by the remote server. See https://w3c.github.io/webdriver/#capabilities
     - command_executor - remote_connection.RemoteConnection object used to execute commands.
     - error_handler - errorhandler.ErrorHandler object used to handle errors.
    """

    _web_element_cls = WebElement

    @classmethod
    async def create(cls, **kwargs): 
        """ Generic method that can be used to create instance of any WebDriver and also start corresponding driver service with new session """
        webdriver_instance = None
        try:
            webdriver_instance = cls(**kwargs)
            service_starter = webdriver_instance.start_service
            if inspect.iscoroutinefunction(service_starter):
                await service_starter()
            #not really clear why this is here, taken from original impl
            start_client = webdriver_instance.start_client
            if inspect.iscoroutinefunction(start_client):
                await start_client()
            elif callable(start_client):
                start_client()
            await webdriver_instance.start_session()
            return webdriver_instance
        finally:
            try:
                if webdriver_instance is not None:
                    quit_ = webdriver_instance.quit
                    if inspect.iscoroutinefunction(quit_):
                        await quit_()
                    elif callable(quit_):
                        quit_()
            except:
                pass

    def __init__(
        self,
        command_codec = None,
        server_url = None,
        desired_capabilities = None,
        browser_profile = None,
        proxy = None,
        keep_alive = True,
        file_detector = None,
        options = None,
        **kwargs
    ):
        """ Create a new driver that will issue commands using the wire protocol.

        :Args:
         - command_codec - An object of type CommandCodec that holds command to url path parsing logic.
                           Default - Based on browser or CommandCodec
         - server_url - URL string for the remote server that has valid hostname.
                        Default - http://127.0.0.1:4444
         - desired_capabilities - A dictionary of capabilities to request when starting the browser session.
         - browser_profile - A selenium.webdriver.firefox.firefox_profile.FirefoxProfile object (only used if Firefox is requested)
         - proxy - A selenium.webdriver.common.proxy.Proxy object. The browser session will be started with given proxy settings, if possible.
         - keep_alive - Whether to configure remote_connection.RemoteConnection to use HTTP keep-alive.
                        Default - True.
         - file_detector - Pass custom file detector object during instantiation.
                           Default - LocalFileDetector()
         - options - An object of type BaseOptions
        """
        #set defaults
        self._server_url = server_url or "http://127.0.0.1:4444"
        self.user_capabilities = {}
        self.user_capabilities_w3c = {}
        self.server_capabilities = {}
        self._set_user_capabilities(options, desired_capabilities, browser_profile)
        self._is_remote = True
        self._switch_to = SwitchTo(self)
        self._mobile = Mobile(self)
        self.session_id = None
        self.command_codec = command_codec or self._determine_command_codec(self.user_capabilities)
        self._http_executor = HttpExecutor(self, self.command_codec, base_url=server_url, keep_alive=keep_alive)
        self.error_handler = ErrorHandler()
        self._w3c = True
        super().__init__(file_detector=file_detector)
    
    @property
    def w3c(self):
        return self._w3c
    
    @property
    def is_remote(self):
        return self._is_remote
    
    @property
    def server_url(self):
        return self._server_url
    
    @server_url.setter
    def server_url(self, url):
        if url is not None:
            self._server_url = url
            self._http_executor.base_url = url
    
    @property
    def mobile(self):
        return self._mobile

    @property
    def name(self):
        """Returns the name of the underlying browser for this instance.

        :Usage:
            ::

                name = driver.name
        """
        if 'browserName' in self.server_capabilities:
            return self.server_capabilities['browserName']
        else:
            raise KeyError("browserName not specified in session capabilities")

    def __repr__(self):
        return f"<{type(self).__module__}.{type(self).__name__} (session = {self.session_id})>"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        await self.quit()
    
    async def start_session(self):
        """ Creates a new session with the desired capabilities """
        parameters = {'capabilities': self.user_capabilities_w3c,
                      'desiredCapabilities': self.user_capabilities}
        
        response = await self.execute(Command.NEW_SESSION, params=parameters)
        if 'sessionId' not in response:
            response = response.get('value') or response
        self.session_id = response.get('sessionId')
        if not self.session_id:
            raise WebDriverException("Remote server didn't respond with sessionId during start session")
        
        self.server_capabilities = response.get('value')
        # if capabilities is none we are probably speaking to a W3C endpoint
        if not self.server_capabilities:
            self.server_capabilities = response.get('capabilities')
        # Double check to see if we have a W3C Compliant browser
        self._w3c = response.get('status') is None
        self._http_executor.w3c = self._w3c
    
    async def execute(
        self,
        driver_command,
        params = None
    ):
        """ Sends a command to be executed by a HttpExecutor.

        :Args:
         - driver_command: A valid Command to execute.
         - params: A dictionary of named parameters to send with the command.

        :Returns:
          The command's JSON response loaded into a dictionary object.
        """
        response = await self._http_executor.execute(driver_command, self.session_id, params)
        if response:
            #TODO - perhaps move to error handler
            #if "value" not in response:
            #    raise WebDriverException("Server did not respond with valid value")
            return response
        # If the server doesn't send a response, assume the command was a success
        return {'success': 0, 'value': None, 'sessionId': self.session_id}
    
    @async_property
    async def title(self):
        """Returns the title of the current page.

        :Usage:
            ::
                title = driver.title
        """
        response = await self.execute(Command.GET_TITLE)
        return response['value'] or ""

    async def get(self, url):
        """ Loads a web page in the current browser session """
        await self.execute(Command.GET, params={'url': url})

    async def execute_script(self, script, *args):
        """ Synchronously Executes JavaScript in the current window/frame.

        :Args:
         - script: The JavaScript to execute.
         - \\*args: Any applicable arguments for your JavaScript.

        :Usage:
            ::

                driver.execute_script('return document.title;')
        """
        converted_args = list(args)
        command = None
        if self._w3c:
            command = Command.W3C_EXECUTE_SCRIPT
        else:
            command = Command.EXECUTE_SCRIPT

        response = await self.execute(command, params = {'script': script, 'args': converted_args})
        return response['value']

    async def execute_async_script(self, script, *args):
        """
        Asynchronously Executes JavaScript in the current window/frame.

        :Args:
         - script: The JavaScript to execute.
         - \\*args: Any applicable arguments for your JavaScript.

        :Usage:
            ::

                script = "var callback = arguments[arguments.length - 1]; " \\
                         "window.setTimeout(function(){ callback('timeout') }, 3000);"
                driver.execute_async_script(script)
        """
        converted_args = list(args)
        if self._w3c:
            command = Command.W3C_EXECUTE_SCRIPT_ASYNC
        else:
            command = Command.EXECUTE_ASYNC_SCRIPT

        response = await self.execute(command, params = {'script': script, 'args': converted_args})
        return response['value']

    @async_property
    async def current_url(self):
        """
        Gets the URL of the current page.

        :Usage:
            ::

                driver.current_url
        """
        response = await self.execute(Command.GET_CURRENT_URL)
        return response['value']

    @async_property
    async def page_source(self):
        """
        Gets the source of the current page.

        :Usage:
            ::

                driver.page_source
        """
        response = await self.execute(Command.GET_PAGE_SOURCE)
        return response['value']

    async def close(self):
        """ Closes the current window.

        :Usage:
            ::

                driver.close()
        """
        await self.execute(Command.CLOSE)

    async def quit(self):
        """ Quits the driver and closes every associated window.

        :Usage:
            ::

                driver.quit()
        """
        try:
            if self.session_id:
                await self.execute(Command.QUIT)
        finally:
            if inspect.iscoroutinefunction(self.stop_client):
                await self.stop_client()
            elif callable(self.stop_client):
                self.stop_client()
            await self._http_executor.close()

    @async_property
    async def current_window_handle(self):
        """ Returns the handle of the current window.

        :Usage:
            ::

                driver.current_window_handle
        """
        if self._w3c:
            command = Command.W3C_GET_CURRENT_WINDOW_HANDLE
        else:
            command = Command.GET_CURRENT_WINDOW_HANDLE
        response = await self.execute(command)
        return response['value']

    @async_property
    async def window_handles(self):
        """ Returns the handles of all windows within the current session.

        :Usage:
            ::

                driver.window_handles
        """
        if self._w3c:
            command = Command.W3C_GET_WINDOW_HANDLES
        else:
            command = Command.GET_WINDOW_HANDLES
        response = await self.execute(command)
        return response.get('value', [])

    async def maximize_window(self):
        """ Maximizes the current window that webdriver is using """
        params = None
        if self._w3c:
            command = Command.W3C_MAXIMIZE_WINDOW
        else:
            command = Command.MAXIMIZE_WINDOW
            params = {'windowHandle': "current"}
        await self.execute(command, params)

    async def fullscreen_window(self):
        """ Invokes the window manager-specific 'full screen' operation """
        await self.execute(Command.FULLSCREEN_WINDOW)

    async def minimize_window(self):
        """ Invokes the window manager-specific 'minimize' operation """
        await self.execute(Command.MINIMIZE_WINDOW)

    @property
    def switch_to(self):
        """
        :Returns:
            - SwitchTo: an object containing all options to switch focus into

        :Usage:
            ::

                element = driver.switch_to.active_element
                alert = driver.switch_to.alert
                driver.switch_to.default_content()
                driver.switch_to.frame('frame_name')
                driver.switch_to.frame(1)
                driver.switch_to.frame(driver.find_elements_by_tag_name("iframe")[0])
                driver.switch_to.parent_frame()
                driver.switch_to.window('main')
        """
        return self._switch_to

    # Navigation
    async def back(self):
        """ Goes one step backward in the browser history.

        :Usage:
            ::

                driver.back()
        """
        await self.execute(Command.GO_BACK)

    async def forward(self):
        """ Goes one step forward in the browser history.

        :Usage:
            ::

                driver.forward()
        """
        await self.execute(Command.GO_FORWARD)

    async def refresh(self):
        """ Refreshes the current page.

        :Usage:
            ::

                driver.refresh()
        """
        await self.execute(Command.REFRESH)

    # Options
    async def get_cookies(self):
        """ Returns a set of dictionaries, corresponding to cookies visible in the current session.

        :Usage:
            ::

                driver.get_cookies()
        """
        response = await self.execute(Command.GET_ALL_COOKIES)
        return response.get('value', [])

    async def get_cookie(self, name):
        """ Get a single cookie by name. Returns the cookie if found, None if not.

        :Usage:
            ::

                driver.get_cookie('my_cookie')
        """
        if self._w3c:
            try:
                response = await self.execute(Command.GET_COOKIE, {'name': name})
                return response['value']
            except NoSuchCookieException:
                return None
        else:
            cookies = await self.get_cookies()
            for cookie in cookies:
                if cookie['name'] == name:
                    return cookie
            return None

    async def delete_cookie(self, name):
        """ Deletes a single cookie with the given name.

        :Usage:
            ::

                driver.delete_cookie('my_cookie')
        """
        await self.execute(Command.DELETE_COOKIE, {'name': name})

    async def delete_all_cookies(self):
        """ Delete all cookies in the scope of the session.

        :Usage:
            ::

                driver.delete_all_cookies()
        """
        await self.execute(Command.DELETE_ALL_COOKIES)

    async def add_cookie(self, cookie_dict):
        """ Adds a cookie to your current session.

        :Args:
         - cookie_dict: A dictionary object, with required keys - "name" and "value";
            optional keys - "path", "domain", "secure", "expiry", "sameSite"

        Usage:
            driver.add_cookie({'name' : 'foo', 'value' : 'bar'})
            driver.add_cookie({'name' : 'foo', 'value' : 'bar', 'path' : '/'})
            driver.add_cookie({'name' : 'foo', 'value' : 'bar', 'path' : '/', 'secure':True})
            driver.add_cookie({'name': 'foo', 'value': 'bar', 'sameSite': 'Strict'})

        """
        if 'sameSite' in cookie_dict:
            if cookie_dict['sameSite'] not in ["Strict", "Lax"]:
                raise ValueError(f"Invalid sameSite cookie value {cookie_dict['sameSite']}")
        await self.execute(Command.ADD_COOKIE, {'cookie': cookie_dict})

    # Timeouts
    async def implicitly_wait(self, time_to_wait):
        """ Sets a sticky timeout to implicitly wait for an element to be found,
           or a command to complete. This method only needs to be called one
           time per session. To set the timeout for calls to
           execute_async_script, see set_script_timeout.

        :Args:
         - time_to_wait: Amount of time to wait (in seconds)

        :Usage:
            ::

                driver.implicitly_wait(30)
        """
        if self._w3c:
            timeout_ms = int(float(time_to_wait) * 1000)
            await self.execute(Command.SET_TIMEOUTS, params={'implicit': timeout_ms})
        else:
            timeout_ms = float(time_to_wait) * 1000
            await self.execute(Command.IMPLICIT_WAIT, params={'ms': timeout_ms})

    async def set_script_timeout(self, time_to_wait):
        """ Set the amount of time that the script should wait during an
           execute_async_script call before throwing an error.

        :Args:
         - time_to_wait: The amount of time to wait (in seconds)

        :Usage:
            ::

                driver.set_script_timeout(30)
        """
        if self._w3c:
            timeout_ms = int(float(time_to_wait) * 1000)
            await self.execute(Command.SET_TIMEOUTS, {'script': timeout_ms})
        else:
            timeout_ms = float(time_to_wait) * 1000
            await self.execute(Command.SET_SCRIPT_TIMEOUT, {'ms': timeout_ms})

    async def set_page_load_timeout(self, time_to_wait):
        """ Set the amount of time to wait for a page load to complete
           before throwing an error.

        :Args:
         - time_to_wait: The amount of time to wait

        :Usage:
            ::

                driver.set_page_load_timeout(30)
        """
        try:
            timeout_ms = int(float(time_to_wait) * 1000)
            await self.execute(Command.SET_TIMEOUTS, {'pageLoad': timeout_ms})
        except WebDriverException:
            timeout_ms = float(time_to_wait) * 1000
            await self.execute(Command.SET_TIMEOUTS, {'ms': timeout_ms, 'type': "page load"})

    @async_property
    async def timeouts(self):
        """ Get all the timeouts that have been set on the current session (in seconds)

        :Usage:
            ::
                driver.timeouts
        :rtype: Timeout
        """
        response = await self.execute(Command.GET_TIMEOUTS)
        timeouts = response['value']
        implicit_wait = timeouts.get('implicit', 0) / 1000
        page_load = timeouts.pgetop('pageLoad', 0) / 1000
        script = timeouts.pop('script', 0) / 1000
        return Timeouts(implicit_wait=implicit_wait, page_load=page_load, script=script)

    async def set_timeouts(self, timeouts):
        """
        Set all timeouts for the session. This will override any previously set timeouts.

        :Usage:
            ::
                my_timeouts = Timeouts()
                my_timeouts.implicit_wait = 10
                driver.timeouts = my_timeouts
        """
        response = await self.execute(Command.SET_TIMEOUTS, timeouts._to_json())
        return response['value']

    async def find_element(self, by=By.ID, value=None):
        """ Find an element given a By strategy and locator. Default By is By.ID

        :Usage:
            ::
                element = driver.find_element(By.ID, 'foo')

        :rtype: WebElement
        """
        by, value = By.get_w3caware_by_value(by, value, self._w3c)
        response = await self.execute(Command.FIND_ELEMENT, {'using': by, 'value': value})
        return response.get('value')

    async def find_elements(self, by=By.ID, value=None):
        """ Find elements given a By strategy and locator. Default By is By.ID

        :Usage:
            ::
                elements = driver.find_elements(By.CLASS_NAME, 'foo')

        :rtype: list of WebElement
        """
        #TODO - check on this. No idea how this functions
        if isinstance(by, RelativeBy):
            _pkg = '.'.join(__name__.split('.')[:-1])
            raw_function = pkgutil.get_data(_pkg, "findElements.js").decode("utf8")
            find_element_js = f"return ({raw_function}).apply(null, arguments);"
            return await self.execute_script(find_element_js, by.to_dict())

        by, value = By.get_w3caware_by_value(by, value, self._w3c)

        # Return empty list if driver returns no value
        response = await self.execute(Command.FIND_ELEMENTS, {'using': by, 'value': value})
        return response.get('value', [])
    
    async def get_screenshot_as_file(self, filename):
        """ Saves a screenshot of the current window to a PNG image file. Returns
           False if there is any IOError, else returns True. Use full paths in
           your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to. This
           should end with a `.png` extension.

        :Usage:
            ::

                driver.get_screenshot_as_file('/Screenshots/foo.png')
        """
        if not filename.lower().endswith('.png'):
            warnings.warn("name used for saved screenshot does not match file "
                          "type. It should end with a `.png` extension", UserWarning)
        png_file = await self.get_screenshot_as_png()
        try:
            async with open(filename, mode="wb") as fd:
                await fd.write(png_file)
        except IOError:
            return False
        finally:
            del png_file
        return True

    async def save_screenshot(self, filename):
        """ Saves a screenshot of the current window to a PNG image file. Returns
           False if there is any IOError, else returns True. Use full paths in
           your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to. This
           should end with a `.png` extension.

        :Usage:
            ::

                driver.save_screenshot('/Screenshots/foo.png')
        """
        response = await self.get_screenshot_as_file(filename)
        return response

    async def get_screenshot_as_png(self):
        """ Gets the screenshot of the current window as a binary data.

        :Usage:
            ::

                driver.get_screenshot_as_png()
        """
        base64_screenshot = await self.get_screenshot_as_base64().encode("ascii")
        return base64.b64decode(base64_screenshot)

    async def get_screenshot_as_base64(self):
        """ Gets the screenshot of the current window as a base64 encoded string
           which is useful in embedded images in HTML.

        :Usage:
            ::

                driver.get_screenshot_as_base64()
        """
        response = await self.execute(Command.SCREENSHOT)
        return response['value']

    async def set_window_size(self, width, height, windowHandle="current"):
        """ Sets the width and height of the current window. (window.resizeTo)

        :Args:
         - width: the width in pixels to set the window to
         - height: the height in pixels to set the window to

        :Usage:
            ::

                driver.set_window_size(800,600)
        """
        if self._w3c:
            if windowHandle != "current":
                warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
            await self.set_window_rect(width=int(width), height=int(height))
        else:
            await self.execute(Command.SET_WINDOW_SIZE, 
                              params = {'width': int(width), 'height': int(height), 'windowHandle': windowHandle})

    async def get_window_size(self, windowHandle="current"):
        """ Gets the width and height of the current window.

        :Usage:
            ::

                driver.get_window_size()
        """
        if self._w3c:
            if windowHandle != "current":
                warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
            size = await self.get_window_rect()
        else:
            size = await self.execute(Command.GET_WINDOW_SIZE, {'windowHandle': windowHandle})
            if size.get('value', None) is not None:
                size = size['value']
        return {k: size[k] for k in ('width', 'height')}

    async def set_window_position(self, x, y, windowHandle="current"):
        """ Sets the x,y position of the current window. (window.moveTo)

        :Args:
         - x: the x-coordinate in pixels to set the window position
         - y: the y-coordinate in pixels to set the window position

        :Usage:
            ::

                driver.set_window_position(0,0)
        """
        if self._w3c:
            if windowHandle != "current":
                warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
            response = await self.set_window_rect(x=int(x), y=int(y))
            return response
        else:
            await self.execute(Command.SET_WINDOW_POSITION,
                               params={'x': int(x), 'y': int(y), 'windowHandle': windowHandle})

    async def get_window_position(self, windowHandle="current"):
        """  Gets the x,y position of the current window.

        :Usage:
            ::

                driver.get_window_position()
        """
        if self._w3c:
            if windowHandle != "current":
                warnings.warn("Only 'current' window is supported for W3C compatibile browsers.")
            position = await self.get_window_rect()
        else:
            response = await self.execute(Command.GET_WINDOW_POSITION, params={'windowHandle': windowHandle})
            position = response['value']
        return {k: position[k] for k in ('x', 'y')}

    async def get_window_rect(self):
        """
        Gets the x, y coordinates of the window as well as height and width of
        the current window.

        :Usage:
            ::

                driver.get_window_rect()
        """
        response = await self.execute(Command.GET_WINDOW_RECT)
        return response['value']

    async def set_window_rect(self, x=None, y=None, width=None, height=None):
        """ Sets the x, y coordinates of the window as well as height and width of
        the current window. This method is only supported for W3C compatible
        browsers; other browsers should use `set_window_position` and
        `set_window_size`.

        :Usage:
            ::

                driver.set_window_rect(x=10, y=10)
                driver.set_window_rect(width=100, height=200)
                driver.set_window_rect(x=10, y=10, width=100, height=200)
        """
        if not self._w3c:
            raise UnknownMethodException("set_window_rect is only supported for W3C compatible browsers")

        if (x is None and y is None) and (height is None and width is None):
            raise InvalidArgumentException("x and y or height and width need values")
        
        response = await self.execute(Command.SET_WINDOW_RECT,
                                     params = {'x': x, 'y': y, 'width': width, 'height': height})
        #TODO - check if this should return
        return response['value']
    
    @async_property
    async def orientation(self):
        """ Gets the current orientation of the device

        :Usage:
            ::

                orientation = driver.orientation
        """
        response = await self.execute(Command.GET_SCREEN_ORIENTATION)
        return response['value']

    async def set_orientation(self, value):
        """
        Sets the current orientation of the device

        :Args:
         - value: orientation to set it to.

        :Usage:
            ::

                driver.orientation = 'landscape'
        """
        allowed_values = ['LANDSCAPE', 'PORTRAIT']
        if value.upper() in allowed_values:
           await  self.execute(Command.SET_SCREEN_ORIENTATION, {'orientation': value})
        else:
            raise WebDriverException(f"{value} is invalid. You can only set the orientation to 'LANDSCAPE' or 'PORTRAIT'")

    @async_property
    async def log_types(self):
        """
        Gets a list of the available log types. This only works with w3c compliant browsers.

        :Usage:
            ::

                driver.log_types
        """
        if self._w3c:
            response = await self.execute(Command.GET_AVAILABLE_LOG_TYPES)
            return response['value']
        return []

    async def get_log(self, log_type):
        """ Gets the log for a given log type

        :Args:
         - log_type: type of log that which will be returned

        :Usage:
            ::

                driver.get_log('browser')
                driver.get_log('driver')
                driver.get_log('client')
                driver.get_log('server')
        """
        response = await self.execute(Command.GET_LOG, {'type': log_type})
        return response['value']
    
    @property
    def desired_capabilities(self):
        """
        returns the drivers current desired capabilities being used
        """
        return self.server_capabilities
    
    def _set_user_capabilities(self, options, desired_capabilities, browser_profile):
        capabilities = {}
        if options is not None:
            capabilities = options.to_capabilities()
        if desired_capabilities is not None:
            if not isinstance(desired_capabilities, dict):
                raise WebDriverException("Provided desired capabilities must be a dictionary")
            else:
                capabilities.update(desired_capabilities)
        if browser_profile:
            if "moz:firefoxOptions" in capabilities:
                capabilities['moz:firefoxOptions']['profile'] = browser_profile.encoded
            else:
                capabilities.update({'firefox_profile': browser_profile.encoded})
        self.user_capabilities = capabilities
        self.user_capabilities_w3c = self._make_w3c_capabilities(capabilities)
 