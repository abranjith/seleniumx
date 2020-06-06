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

from async_property import async_property

from seleniumx.webdriver.common.by import By
from seleniumx.common.exceptions import NoSuchElementException, UnexpectedTagNameException

class Select(object):

    def __init__(
        self,
        webelement
    ):
        """ Constructor. A check is made that the given element is, indeed, a SELECT tag. If it is not,
        then an UnexpectedTagNameException is thrown.

        :Args:
         - webelement - element SELECT element to wrap

        Example:
            from selenium.webdriver.support.ui import Select \n
            Select(driver.find_element(By.TAG_NAME, "select")).select_by_index(2)
        """
        if webelement.tag_name.lower() != "select":
            raise UnexpectedTagNameException(f"Select only works on <select> elements, not on <{webelement.tag_name}>")
        self._element = webelement
        multi = self._element.get_attribute("multiple")
        self.is_multiple = multi and multi != "false"

    @async_property
    async def options(self):
        """Returns a list of all options belonging to this select tag"""
        return await self._element.find_elements(By.TAG_NAME, "option")

    @async_property
    def all_selected_options(self):
        """Returns a list of all selected options belonging to this select tag"""
        selected_options = []
        all_options = await self.options
        async for option in all_options:
            if await option.is_selected():
                selected_options.append(option)
        return selected_options

    @async_property
    async def first_selected_option(self):
        """The first selected option in this select tag (or the currently selected option in a
        normal select)"""
        all_options = await self.options
        async for option in all_options:
            if await option.is_selected():
                return option
        raise NoSuchElementException("No options are selected")

    async def select_by_value(self, value):
        """Select all options that have a value matching the argument. That is, when given "foo" this
           would select an option like:

           <option value="foo">Bar</option>

           :Args:
            - value - The value to match against

           throws NoSuchElementException If there is no option with specified value in SELECT
           """
        value = self._escape_string(value)
        css = f"option[value ={value}]"
        options = await self._element.find_elements(By.CSS_SELECTOR, css)
        matched = False
        async for option in options:
            await self._set_selected(option)
            if not self.is_multiple:
                return
            matched = True
        if not matched:
            raise NoSuchElementException(f"Cannot locate option with value: {value}")

    async def select_by_index(self, index):
        """Select the option at the given index. This is done by examing the "index" attribute of an
           element, and not merely by counting.

           :Args:
            - index - The option at this index will be selected

           throws NoSuchElementException If there is no option with specified index in SELECT
           """
        match = str(index)
        all_options = await self.options
        async for option in all_options:
            if option.get_attribute("index") == match:
                await self._set_selected(option)
                return
        raise NoSuchElementException(f"Could not locate element with index {index}")

    async def select_by_visible_text(self, text):
        """Select all options that display text matching the argument. That is, when given "Bar" this
           would select an option like:

            <option value="foo">Bar</option>

           :Args:
            - text - The visible text to match against

            throws NoSuchElementException If there is no option with specified text in SELECT
           """
        value = self._escape_string(text)
        xpath = f".//option[normalize-space(.)={value}]"
        options = await self._element.find_elements(By.XPATH, xpath)
        matched = False
        async for option in options:
            await self._set_selected(option)
            if not self.is_multiple:
                return
            matched = True

        if len(options) == 0 and " " in text:
            substring_without_space = self._get_longest_token(text)
            if substring_without_space == "":
                candidates = await self.options
            else:
                value = self._escape_string(substring_without_space)
                xpath = f".//option[contains(.,{value})]"
                candidates = await self._element.find_elements(By.XPATH, xpath)
            async for candidate in candidates:
                if text == await candidate.text:
                    await self._set_selected(candidate)
                    if not self.is_multiple:
                        return
                    matched = True

        if not matched:
            raise NoSuchElementException(f"Could not locate element with visible text: {text}")

    async def deselect_all(self):
        """Clear all selected entries. This is only valid when the SELECT supports multiple selections.
           throws NotImplementedError If the SELECT does not support multiple selections
        """
        if not self.is_multiple:
            raise NotImplementedError("You may only deselect all options of a multi-select")
        options = await self.options 
        async for option in options:
            await self._unset_selected(option)

    async def deselect_by_value(self, value):
        """Deselect all options that have a value matching the argument. That is, when given "foo" this
           would deselect an option like:

            <option value="foo">Bar</option>

           :Args:
            - value - The value to match against

            throws NoSuchElementException If there is no option with specified value in SELECT
        """
        if not self.is_multiple:
            raise NotImplementedError("You may only deselect options of a multi-select")
        matched = False
        value = self._escape_string(value)
        css = f"option[value = {value}]"
        options = await self._element.find_elements(By.CSS_SELECTOR, css)
        async for option in options:
            await self._unset_selected(option)
            matched = True
        if not matched:
            raise NoSuchElementException(f"Could not locate element with value: {value}")

    async def deselect_by_index(self, index):
        """Deselect the option at the given index. This is done by examing the "index" attribute of an
           element, and not merely by counting.

           :Args:
            - index - The option at this index will be deselected

            throws NoSuchElementException If there is no option with specified index in SELECT
        """
        if not self.is_multiple:
            raise NotImplementedError("You may only deselect options of a multi-select")
        options = await self.options 
        async for option in options:
            if option.get_attribute("index") == str(index):
                await self._unset_selected(option)
                return
        raise NoSuchElementException(f"Could not locate element with index {index}")

    async def deselect_by_visible_text(self, text):
        """Deselect all options that display text matching the argument. That is, when given "Bar" this
           would deselect an option like:

           <option value="foo">Bar</option>

           :Args:
            - text - The visible text to match against
        """
        if not self.is_multiple:
            raise NotImplementedError("You may only deselect options of a multi-select")
        matched = False
        value = self._escape_string(text)
        xpath = f".//option[normalize-space(.)={value}]"
        options = await self._element.find_elements(By.XPATH, xpath)
        async for option in options:
            await self._unset_selected(option)
            matched = True
        if not matched:
            raise NoSuchElementException(f"Could not locate element with visible text: {text}")

    async def _set_selected(self, option):
        if not await option.is_selected():
            await option.click()

    async def _unset_selected(self, option):
        if await option.is_selected():
            await option.click()

    def _escape_string(self, value):
        if '"' in value and "'" in value:
            substrings = value.split("\"")
            result = ["concat("]
            for substring in substrings:
                result.append(f"\"{substring}\"")
                result.append(", '\"', ")
            result = result[0:-1]
            if value.endswith('"'):
                result.append(", '\"'")
            return "".join(result) + ")"

        if '"' in value:
            return f"'{value}'"

        return f"\"{value}\""

    def _get_longest_token(self, value):
        items = value.split(" ")
        longest = max(items, key = lambda s : len(s))
        return longest
