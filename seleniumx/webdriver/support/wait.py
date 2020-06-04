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

import time
import inspect
import asyncio

from seleniumx.common.exceptions import NoSuchElementException, TimeoutException

class WebDriverWait(object):

    POLL_FREQUENCY = 0.5        # How long to sleep in between retry calls
    DEFAULT_IGNORED_EXCEPTIONS = [NoSuchElementException]      # exceptions ignored during calls to the method

    def __init__(
        self,
        driver,
        timeout,
        poll_frequency = None,
        ignored_exceptions = None):
        """Constructor, takes a WebDriver instance and timeout in seconds.

           :Args:
            - driver - Instance of WebDriver (Ie, Firefox, Chrome or Remote)
            - timeout - Number of seconds before timing out
            - poll_frequency - sleep interval between calls
              By default, it is 0.5 second.
            - ignored_exceptions - iterable structure of exception classes ignored during calls.
              By default, it contains NoSuchElementException only.

           Example::

            from selenium.webdriver.support.wait import WebDriverWait \n
            element = WebDriverWait(driver, 10).until(lambda x: x.find_element(By.ID, "someId")) \n
            is_disappeared = WebDriverWait(driver, 30, 1, (ElementNotVisibleException)).\\ \n
                        until_not(lambda x: x.find_element(By.ID, "someId").is_displayed())
        """
        self._driver = driver
        self._timeout = float(timeout)
        self._poll = poll_frequency or WebDriverWait.POLL_FREQUENCY
        # avoid the divide by zero
        if self._poll <= 0:
            self._poll = WebDriverWait.POLL_FREQUENCY
        exceptions = WebDriverWait.DEFAULT_IGNORED_EXCEPTIONS
        exceptions = self._extend_ignored_exceptions(exceptions, ignored_exceptions)
        self._ignored_exceptions = tuple(exceptions)

    def __repr__(self):
        return f'<{type(self).__module__}.{type(self).__name__} (session="{self._driver.session_id}")>'
    
    def add_ignored_exceptions(self, ignored_exceptions):
        exceptions = self._extend_ignored_exceptions(list(self._ignored_exceptions), ignored_exceptions)
        self._ignored_exceptions = tuple(exceptions)

    def remove_ignored_exceptions(self, ignored_exceptions):
        if not ignored_exceptions:
            return
        if isinstance(ignored_exceptions, (list, tuple, set)):
            ignored_exceptions = list(ignored_exceptions)
        else:
            ignored_exceptions = [ignored_exceptions]
        exceptions = list(self._ignored_exceptions)
        exceptions_copy = exceptions[:]
        for ex in exceptions:
            if ex in ignored_exceptions:
                exceptions_copy.remove(ex)
        self._ignored_exceptions = tuple(exceptions_copy)
    
    def _extend_ignored_exceptions(self, current, ignored_exceptions):
        if not ignored_exceptions:
            return current
        if isinstance(ignored_exceptions, (list, tuple, set)):
            ignored_exceptions = list(ignored_exceptions)
        else:
            ignored_exceptions = [ignored_exceptions]
        current.extend(ignored_exceptions)
        #remoe duplicates
        current = list(set(current))
        return current

    async def until(
        self,
        method,
        message = ""
    ):
        """Calls the method provided with the driver as an argument until the \
        return value does not evaluate to ``False``.

        :param method: callable(WebDriver)
        :param message: optional message for :exc:`TimeoutException`
        :returns: the result of the last call to `method`
        :raises: :exc:`selenium.common.exceptions.TimeoutException` if timeout occurs
        """
        screen = None
        stacktrace = None

        end_time = time.time() + self._timeout
        while True:
            try:
                value = await self._fn_orchestrator(method, self._driver)
                if value:
                    return value
            except self._ignored_exceptions as ex:          # pylint: disable=catching-non-exception
                screen = getattr(ex, "screen", None)
                stacktrace = getattr(ex, "stacktrace", None)
            await asyncio.sleep(self._poll)
            if time.time() > end_time:
                break
        raise TimeoutException(message, screen, stacktrace)

    async def until_not(
        self,
        method,
        message = ""):
        """Calls the method provided with the driver as an argument until the \
        return value evaluates to ``False``.

        :param method: callable(WebDriver)
        :param message: optional message for :exc:`TimeoutException`
        :returns: the result of the last call to `method`, or
                  ``True`` if `method` has raised one of the ignored exceptions
        :raises: :exc:`selenium.common.exceptions.TimeoutException` if timeout occurs
        """
        screen = None
        stacktrace = None

        end_time = time.time() + self._timeout
        while True:
            try:
                value = await self._fn_orchestrator(method, self._driver)
                if not value:
                    return value
            except self._ignored_exceptions as ex:        # pylint: disable=catching-non-exception
                screen = getattr(ex, "screen", None)
                stacktrace = getattr(ex, "stacktrace", None)
            await asyncio.sleep(self._poll)
            if time.time() > end_time:
                break
        raise TimeoutException(message, screen, stacktrace)

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