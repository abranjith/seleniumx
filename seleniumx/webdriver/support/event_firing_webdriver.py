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


import inspect
from functools import update_wrapper

from seleniumx.common.exceptions import WebDriverException
from seleniumx.webdriver.common.by import By
from seleniumx.webdriver.remote.webdriver import RemoteWebDriver
from seleniumx.webdriver.remote.webelement import WebElement
from seleniumx.webdriver.support.abstract_event_listener import AbstractEventListener


def _wrap_elements(result, ef_driver):
    """ Wraps WebElement object as EventFiringWebElement """
    if isinstance(result, WebElement):
        return EventFiringWebElement(result, ef_driver)
    elif isinstance(result, list):
        return list(_wrap_elements(item, ef_driver) for item in result)
    elif isinstance(result, tuple):
        return tuple(_wrap_elements(item, ef_driver) for item in result)
    else:
        return result

class EventFiringWebDriver(object):
    """ A wrapper around an arbitrary WebDriver instance which supports firing events """

    def __init__(
        self,
        driver,
        event_listener
    ):
        """ Creates a new instance of the EventFiringWebDriver

        :Args:
         - driver : A WebDriver instance
         - event_listener : Instance of a class that subclasses AbstractEventListener and implements it fully or partially

        Example:

        ::

            from selenium.webdriver import Firefox
            from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener

            class MyListener(AbstractEventListener):
                def before_navigate_to(self, url, driver):
                    print("Before navigate to %s" % url)
                def after_navigate_to(self, url, driver):
                    print("After navigate to %s" % url)

            driver = Firefox()
            ef_driver = EventFiringWebDriver(driver, MyListener())
            ef_driver.get("http://www.google.co.in/")
        """
        if not isinstance(driver, RemoteWebDriver):
            raise WebDriverException("A WebDriver instance must be supplied")
        if not isinstance(event_listener, AbstractEventListener):
            raise WebDriverException("Event listener must be a subclass of AbstractEventListener")
        self._driver = driver
        self._listener = event_listener
        self._dispatcher = _Dispatcher(event_listener, self)

    @property
    def wrapped_driver(self):
        """ Returns the WebDriver instance wrapped by this EventsFiringWebDriver """
        return self._driver

    async def get(self, url):
        await self._dispatcher.dispatch(
            self._listener.before_navigate_to,
            self._listener.after_navigate_to,
            (url, self._driver),
            self._driver.get,
            url
        )

    async def back(self):
        await self._dispatcher.dispatch(
            self._listener.before_navigate_back,
            self._listener.after_navigate_back,
            self._driver,
            self._driver.back,
            None
        )

    async def forward(self):
        await self._dispatcher.dispatch(
            self._listener.before_navigate_forward,
            self._listener.after_navigate_forward,
            self._driver,
            self._driver.forward,
            None
        )

    async def execute_script(self, script, *args):
        response = await self._dispatcher.dispatch(
            self._listener.before_execute_script,
            self._listener.after_execute_script,
            (script, self._driver),
            self._driver.execute_script,
            (script, *args)
        )
        return response

    async def execute_async_script(self, script, *args):
        response = await self._dispatcher.dispatch(
            self._listener.before_execute_script,
            self._listener.after_execute_script,
            (script, self._driver),
            self._driver.execute_async_script,
            (script, *args)
        )
        return response

    async def close(self):
        await self._dispatcher.dispatch(
            self._listener.before_close,
            self._listener.after_close,
            self._driver,
            self._driver.close,
            None
        )

    async def quit(self):
        await self._dispatcher.dispatch(
            self._listener.before_quit,
            self._listener.after_quit,
            self._driver,
            self._driver.quit,
            None
        )

    async def find_element(self, by=By.ID_OR_NAME, value=None):
        response = await self._dispatcher.dispatch(
            self._listener.before_find,
            self._listener.after_dind,
            (by, value, self._driver),
            self._driver.find_element,
            (by, value)
        )
        return response


    async def find_elements(self, by=By.ID_OR_NAME, value=None):
        response = await self._dispatcher.dispatch(
            self._listener.before_find,
            self._listener.after_dind,
            (by, value, self._driver),
            self._driver.find_elements,
            (by, value)
        )
        return response

    def __setattr__(self, item, value):
        if item.startswith("_") or not hasattr(self._driver, item):
            object.__setattr__(self, item, value)
        else:
            try:
                object.__setattr__(self._driver, item, value)
            except Exception as ex:
                self._listener.on_exception(ex, self._driver)
                raise ex

    def __getattr__(self, name):
        def _wrap(*args, **kwargs):
            try:
                result = attrib(*args, **kwargs)
                return _wrap_elements(result, self)
            except Exception as ex:
                self._listener.on_exception(ex, self._driver)
                raise ex
        async def _wrap_async(*args, **kwargs):
            try:
                result = await attrib(*args, **kwargs)
                return _wrap_elements(result, self)
            except Exception as ex:
                self._listener.on_exception(ex, self._driver)
                raise ex
        try:
            attrib = getattr(self._driver, name)
            if inspect.iscoroutinefunction(attrib):
                return update_wrapper(_wrap_async, attrib)
            elif callable(attrib):
                return update_wrapper(_wrap, attrib)
            return attrib
        except Exception as ex:
            self._listener.on_exception(ex, self._driver)
            raise ex


class EventFiringWebElement(object):
    """" A wrapper around WebElement instance which supports firing events """

    def __init__(
        self,
        webelement,
        ef_driver
    ):
        """ Creates a new instance of the EventFiringWebElement """
        self._webelement = webelement
        self._ef_driver = ef_driver
        self._driver = ef_driver.wrapped_driver
        self._listener = ef_driver._listener
        self._dispatcher = _Dispatcher(self._listener, ef_driver)

    @property
    def wrapped_element(self):
        """ Returns the WebElement wrapped by this EventFiringWebElement instance """
        return self._webelement

    async def click(self):
        await self._dispatcher.dispatch(
            self._listener.before_click,
            self._listener.after_click,
            (self._webelement, self._driver),
            self._webelement.click,
            None
        )

    async def clear(self):
        await self._dispatcher.dispatch(
            self._listener.before_change_value_of,
            self._listener.after_change_value_of,
            (self._webelement, self._driver),
            self._webelement.clear,
            None
        )

    async def send_keys(self, *value):
        await self._dispatcher.dispatch(
            self._listener.before_change_value_of,
            self._listener.after_change_value_of,
            (self._webelement, self._driver),
            self._webelement.send_keys,
            value
        )

    async def find_element(self, by=By.ID, value=None):
        response = await self._dispatcher.dispatch(
            self._listener.before_find,
            self._listener.after_dind,
            (by, value, self._driver),
            self._webelement.find_element,
            (by, value)
        )
        return response

    async def find_elements(self, by=By.ID, value=None):
        response = await self._dispatcher.dispatch(
            self._listener.before_find,
            self._listener.after_dind,
            (by, value, self._driver),
            self._webelement.find_elements,
            (by, value)
        )
        return response

    def __setattr__(self, item, value):
        if item.startswith("_") or not hasattr(self._webelement, item):
            object.__setattr__(self, item, value)
        else:
            try:
                object.__setattr__(self._webelement, item, value)
            except Exception as ex:
                self._listener.on_exception(ex, self._driver)
                raise ex

    def __getattr__(self, name):
        def _wrap(*args, **kwargs):
            try:
                result = attrib(*args, **kwargs)
                return _wrap_elements(result, self._ef_driver)
            except Exception as e:
                self._listener.on_exception(e, self._driver)
                raise
        
        async def _wrap_async(*args, **kwargs):
            try:
                result = await attrib(*args, **kwargs)
                return _wrap_elements(result, self)
            except Exception as ex:
                self._listener.on_exception(ex, self._driver)
                raise ex

        try:
            attrib = getattr(self._webelement, name)
            if inspect.iscoroutinefunction(attrib):
                return update_wrapper(_wrap_async, attrib)
            elif callable(attrib):
                return update_wrapper(_wrap, attrib)
            return attrib
        except Exception as ex:
            self._listener.on_exception(ex, self._driver)
            raise ex

class _Dispatcher(object):

    def __init__(self, listener, ef_driver):
        self._listener = listener
        self._ef_driver = ef_driver
        self._driver = ef_driver.wrapped_driver
    
    async def dispatch(self, before_func, after_func, listener_args, main_func, main_func_args):
        listener_args = self._ensure_tuple(listener_args)
        main_func_args = self._ensure_tuple(main_func_args)
        await self._fn_orchestrator(before_func, *listener_args)
        try:
            result = await self._fn_orchestrator(main_func, *main_func_args)
        except Exception as ex:
            self._listener.on_exception(ex, self._driver)
            raise ex
        await self._fn_orchestrator(after_func, *listener_args)
        return _wrap_elements(result, self._ef_driver)
    
    #TODO - this can be made a util
    async def _fn_orchestrator(self, fn, *args):
        return_args = None
        if inspect.iscoroutinefunction(fn):
            if args:
                return_args = await fn(*args)
            else:
                return_args = await fn()
        elif callable(fn):
            if args:
                return_args = fn(*args)
            else:
                return_args = fn()
        return return_args
    
    def _ensure_tuple(self, args):
        if not args:
            return ()
        if not isinstance(args, tuple):
            args = (args,)
        return args
