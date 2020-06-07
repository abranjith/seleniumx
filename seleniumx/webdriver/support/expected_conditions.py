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

import re

from seleniumx.common.exceptions import NoSuchElementException
from seleniumx.common.exceptions import NoSuchFrameException
from seleniumx.common.exceptions import StaleElementReferenceException
from seleniumx.common.exceptions import WebDriverException
from seleniumx.common.exceptions import NoAlertPresentException
from seleniumx.webdriver.remote.webdriver import WebElement

class ExpectedConditions(object):

    @staticmethod
    def title_is(title):
        """An expectation for checking the title of a page.
        title is the expected title, which must be an exact match
        returns True if the title matches, false otherwise."""
        async def _predicate(driver):
            actual_title = await driver.title
            return actual_title == title

        return _predicate


    @staticmethod
    def title_contains(title):
        """ An expectation for checking that the title contains a case-sensitive
        substring. title is the fragment of title expected
        returns True when the title matches, False otherwise
        """
        async def _predicate(driver):
            actual_title = await driver.title
            return title in actual_title

        return _predicate


    @staticmethod
    def presence_of_element_located(locator):
        """ An expectation for checking that an element is present on the DOM
        of a page. This does not necessarily mean that the element is visible.
        locator - used to find the element
        returns the WebElement once it is located
        """
        async def _predicate(driver):
            return await driver.find_element(*locator)

        return _predicate


    @staticmethod
    def url_contains(url):
        """ An expectation for checking that the current url contains a
        case-sensitive substring.
        url is the fragment of url expected,
        returns True when the url matches, False otherwise
        """
        async def _predicate(driver):
            actual_url = await driver.current_url
            return url in actual_url

        return _predicate

    @staticmethod
    def url_matches(pattern):
        """An expectation for checking the current url.
        pattern is the expected pattern, which must be an exact match
        returns True if the url matches, false otherwise."""
        async def _predicate(driver):
            actual_url = await driver.current_url
            return re.search(pattern, actual_url) is not None

        return _predicate

    @staticmethod
    def url_to_be(url):
        """An expectation for checking the current url.
        url is the expected url, which must be an exact match
        returns True if the url matches, false otherwise."""
        async def _predicate(driver):
            actual_url = await driver.current_url
            return url == actual_url

        return _predicate

    @staticmethod
    def url_changes(url):
        """An expectation for checking the current url.
        url is the expected url, which must not be an exact match
        returns True if the url is different, false otherwise."""
        async def _predicate(driver):
            actual_url = await driver.current_url
            return url != actual_url

        return _predicate

    @staticmethod
    def visibility_of_element_located(locator):
        """ An expectation for checking that an element is present on the DOM of a
        page and visible. Visibility means that the element is not only displayed
        but also has a height and width that is greater than 0.
        locator - used to find the element
        returns the WebElement once it is located and visible
        """
        async def _predicate(driver):
            try:
                element = await driver.find_element(*locator)
                return await ECS._element_if_visible(element)
            except StaleElementReferenceException:
                return False

        return _predicate


    @staticmethod
    def visibility_of(element):
        """ An expectation for checking that an element, known to be present on the
        DOM of a page, is visible. Visibility means that the element is not only
        displayed but also has a height and width that is greater than 0.
        element is the WebElement
        returns the (same) WebElement once it is visible
        """
        async def _predicate(driver):
            return await ECS._element_if_visible(element)

        return _predicate

    @staticmethod
    async def _element_if_visible(element, visibility=True):
        is_displayed = await element.is_displayed()
        return element if is_displayed == visibility else False

    @staticmethod
    def presence_of_all_elements_located(locator):
        """ An expectation for checking that there is at least one element present
        on a web page.
        locator is used to find the element
        returns the list of WebElements once they are located
        """
        async def _predicate(driver):
            elements = await driver.find_elements(*locator)
            return elements

        return _predicate

    @staticmethod
    def visibility_of_any_elements_located(locator):
        """ An expectation for checking that there is at least one element visible
        on a web page.
        locator is used to find the element
        returns the list of WebElements once they are located
        """
        async def _predicate(driver):
            elements = await driver.find_elements(*locator)
            visible_elements = []
            async for element in elements:
                if await ECS._element_if_visible(element):
                    visible_elements.append(element)
            return visible_elements

        return _predicate

    @staticmethod
    def visibility_of_all_elements_located(locator):
        """ An expectation for checking that all elements are present on the DOM of a
        page and visible. Visibility means that the elements are not only displayed
        but also has a height and width that is greater than 0.
        locator - used to find the elements
        returns the list of WebElements once they are located and visible
        """
        async def _predicate(driver):
            try:
                elements = await driver.find_elements(*locator)
                async for element in elements:
                    if await ECS._element_if_visible(element, visibility=False):
                        return None
                return elements
            except StaleElementReferenceException:
                return None

        return _predicate

    @staticmethod
    def text_to_be_present_in_element(locator, text):
        """ An expectation for checking if the given text is present in the
        specified element.
        locator, text
        """
        async def _predicate(driver):
            try:
                element = await driver.find_element(*locator)
                element_text = await element.text
                return text in element_text
            except StaleElementReferenceException:
                return False

        return _predicate

    @staticmethod
    def text_to_be_present_in_element_value(locator, text):
        """
        An expectation for checking if the given text is present in the element's
        locator, text
        """
        def _predicate(driver):
            try:
                element = await driver.find_element(*locator)
                element_text = await element.get_attribute("value")
                return text in element_text
            except StaleElementReferenceException:
                return False

        return _predicate


    @staticmethod
    def frame_to_be_available_and_switch_to_it(locator):
        """ An expectation for checking whether the given frame is available to
        switch to.  If the frame is available it switches the given driver to the
        specified frame.
        """
        async def _predicate(driver):
            try:
                if hasattr(locator, "__iter__"):
                    element = await driver.find_element(*locator)
                    await driver.switch_to.frame(element)
                else:
                    await driver.switch_to.frame(locator)
                return True
            except NoSuchFrameException:
                return None

        return _predicate


    @staticmethod
    def invisibility_of_element_located(locator):
        """ An Expectation for checking that an element is either invisible or not
        present on the DOM.

        locator used to find the element
        """
        async def _predicate(driver):
            try:
                target = locator
                if not isinstance(target, WebElement):
                    target = await driver.find_element(*target)
                return await ECS._element_if_visible(target, visibility=False)
            except (NoSuchElementException, StaleElementReferenceException):
                # In the case of NoSuchElement, returns true because the element is
                # not present in DOM. The try block checks if the element is present
                # but is invisible.
                # In the case of StaleElementReference, returns true because stale
                # element reference implies that element is no longer visible.
                return True

        return _predicate

    @staticmethod
    def invisibility_of_element(element):
        """ An Expectation for checking that an element is either invisible or not
        present on the DOM.

        element is either a locator (text) or an WebElement
        """
        return ECS.invisibility_of_element_located(element)

    @staticmethod
    def element_to_be_clickable(locator):
        """ An Expectation for checking an element is visible and enabled such that
        you can click it."""
        def _predicate(driver):
            element = await driver.find_element(*locator)
            visible =  await element.is_displayed()
            enabled = await element.is_enabled()
            if element and visible and enabled:
                return element
            else:
                return False

        return _predicate

    @staticmethod
    def staleness_of(element):
        """ Wait until an element is no longer attached to the DOM.
        element is the element to wait for.
        returns False if the element is still attached to the DOM, true otherwise.
        """
        async def _predicate(driver):
            try:
                # Calling any method forces a staleness check
                await element.is_enabled()
                return False
            except StaleElementReferenceException:
                return True

        return _predicate

    @staticmethod
    def element_to_be_selected(element):
        """ An expectation for checking the selection is selected.
        element is WebElement object
        """
        def _predicate(driver):
            return await element.is_selected()

        return _predicate

    @staticmethod
    def element_located_to_be_selected(locator):
        """An expectation for the element to be located is selected.
        locator is a tuple of (by, path)"""
        async def _predicate(driver):
            element = await driver.find_element(*locator)
            return await element.is_selected()

        return _predicate

    @staticmethod
    def element_selection_state_to_be(element, is_selected):
        """ An expectation for checking if the given element is selected.
        element is WebElement object
        is_selected is a Boolean."
        """
        async def _predicate(driver):
            selected = await element.is_selected()
            return selected == is_selected

        return _predicate

    @staticmethod
    def element_located_selection_state_to_be(locator, is_selected):
        """ An expectation to locate an element and check if the selection state
        specified is in that state.
        locator is a tuple of (by, path)
        is_selected is a boolean
        """
        async def _predicate(driver):
            try:
                element = driver.find_element(*locator)
                selected = await element.is_selected()
                return selected == is_selected
            except StaleElementReferenceException:
                return False

        return _predicate

    @staticmethod
    def number_of_windows_to_be(num_windows):
        """ An expectation for the number of windows to be a certain value."""
        async def _predicate(driver):
            window_handles = await driver.window_handles
            return len(window_handles) == num_windows

        return _predicate

    @staticmethod
    def new_window_is_opened(current_handles):
        """ An expectation that a new window will be opened and have the number of
        windows handles increase"""
        async def _predicate(driver):
            window_handles = await driver.window_handles
            return len(window_handles) > len(current_handles)

        return _predicate

    @staticmethod
    def alert_is_present():
        async def _predicate(driver):
            try:
                return await driver.switch_to.alert
            except NoAlertPresentException:
                return None

        return _predicate

    @staticmethod
    def any_of(*expected_conditions):
        """ An expectation that any of multiple expected conditions is true.
        Equivalent to a logical 'OR'.
        Returns results of the first matching condition, or False if none do. """
        async def any_of_condition(driver):
            async for expected_condition in expected_conditions:        # pylint: disable=not-an-iterable
                try:
                    result = await expected_condition(driver)
                    if result:
                        return result
                except WebDriverException:
                    pass
            return False
        return any_of_condition

    @staticmethod
    def all_of(*expected_conditions):
        """ An expectation that all of multiple expected conditions is true.
        Equivalent to a logical 'AND'.
        Returns: When any ExpectedCondition is not met: False.
        When all ExpectedConditions are met: A List with each ExpectedCondition's return value. """
        async def all_of_condition(driver):
            results = []
            async for expected_condition in expected_conditions:        # pylint: disable=not-an-iterable
                try:
                    result = await expected_condition(driver)
                    if not result:
                        return False
                    results.append(result)
                except WebDriverException:
                    return False
            return results
        return all_of_condition

    @staticmethod
    def none_of(*expected_conditions):
        """ An expectation that none of 1 or multiple expected conditions is true.
        Equivalent to a logical 'NOT-OR'.
        Returns a Boolean """
        async def none_of_condition(driver):
            async for expected_condition in expected_conditions:        # pylint: disable=not-an-iterable
                try:
                    result = await expected_condition(driver)
                    if result:
                        return False
                except WebDriverException:
                    pass
            return True
        return none_of_condition


ECS = ExpectedConditions