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
from base64 import encodestring as encodebytes
import hashlib
import pkgutil
import warnings
import zipfile
from io import BytesIO as IOStream

import aiofiles
from async_property import async_property

from seleniumx.common.exceptions import WebDriverException
from seleniumx.webdriver.common.by import By
from seleniumx.webdriver.common.utils import keys_to_typing
from seleniumx.webdriver.common.enums import Command
from seleniumx.webdriver.remote.command import CommandInfo
from seleniumx.webdriver.remote.webdriver import RemoteWebDriver

#TODO - fix this
# not relying on __package__ here as it can be `None` in some situations (see #4558)
#_pkg = '.'.join(__name__.split('.')[:-1])
#getAttribute_js = pkgutil.get_data(_pkg, 'getAttribute.js').decode('utf8')
#isDisplayed_js = pkgutil.get_data(_pkg, 'isDisplayed.js').decode('utf8')
getAttribute_js = ""
isDisplayed_js = ""

class WebElement(object):
    """Represents a DOM element.

    Generally, all interesting operations that interact with a document will be
    performed through this interface.

    All method calls will do a freshness check to ensure that the element
    reference is still valid.  This essentially determines whether or not the
    element is still attached to the DOM.  If this test fails, then an
    ``StaleElementReferenceException`` is thrown, and all future calls to this
    instance will fail."""

    def __init__(
        self,
        parent : RemoteWebDriver,
        id_ : str,
        w3c : bool = False
    ):
        self._parent = parent
        self._id = id_
        self._w3c = w3c
    
    @property
    def parent(self):
        """Internal reference to the WebDriver instance this element was found from."""
        return self._parent

    @property
    def id(self):
        """Internal ID used by selenium.

        This is mainly for internal use. Simple use cases such as checking if 2
        webelements refer to the same element, can be done using ``==``::

            if element1 == element2:
                print("These 2 are equal")

        """
        return self._id

    @async_property
    async def tag_name(self):
        """This element's ``tagName`` property."""
        response = await self._execute(Command.GET_ELEMENT_TAG_NAME)
        return response['value']

    @async_property
    async def text(self):
        """The text of the element."""
        response = await self._execute(Command.GET_ELEMENT_TEXT)
        return response['value']
    
    @async_property
    async def size(self):
        """ The size of the element."""
        command = Command.GET_ELEMENT_RECT if self._w3c else Command.GET_ELEMENT_SIZE
        response = await self._execute(command)
        size = response['value']
        new_size = {'height': size['height'],
                    'width': size['width']}
        return new_size

    async def value_of_css_property(self, property_name):
        """ The value of a CSS property. """
        response = await self._execute(Command.GET_ELEMENT_VALUE_OF_CSS_PROPERTY, {'propertyName': property_name})
        return response['value']

    @async_property
    async def location(self):
        """The location of the element in the renderable canvas."""
        command = Command.GET_ELEMENT_RECT if self._w3c else Command.GET_ELEMENT_LOCATION
        response = await self._execute(command)
        old_loc = response['value']
        new_loc = {'x': round(old_loc['x']),
                   'y': round(old_loc['y'])}
        return new_loc

    @async_property
    async def rect(self):
        """A dictionary with the size and location of the element."""
        if self._w3c:
            response = await self._execute(Command.GET_ELEMENT_RECT)
            return response['value']
        else:
            rect = await self.size.copy()       # pylint: disable=no-member
            rect.update(await self.location)
            return rect
    
    @async_property
    async def location_once_scrolled_into_view(self):
        """ THIS PROPERTY MAY CHANGE WITHOUT WARNING. Use this to discover
        where on the screen an element is so that we can click it. This method
        should cause the element to be scrolled into view.

        Returns the top lefthand corner location on the screen, or ``None`` if
        the element is not visible.

        """
        if self._w3c:
            response = await self._execute(Command.W3C_EXECUTE_SCRIPT, {
                'script': "arguments[0].scrollIntoView(true); return arguments[0].getBoundingClientRect()",
                'args': [self]})
            old_loc = response['value']
            return {'x': round(old_loc['x']),
                    'y': round(old_loc['y'])}
        else:
            response = await self._execute(Command.GET_ELEMENT_LOCATION_ONCE_SCROLLED_INTO_VIEW)
            return response['value']

    async def click(self):
        """Clicks the element."""
        await self._execute(Command.CLICK_ELEMENT)

    async def submit(self):
        """Submits a form."""
        if self._w3c:
            form = await self.find_element(By.XPATH, "./ancestor-or-self::form")
            await self._parent.execute_script(
                "var e = arguments[0].ownerDocument.createEvent('Event');"
                "e.initEvent('submit', true, true);"
                "if (arguments[0].dispatchEvent(e)) { arguments[0].submit() }", form)
        else:
            await self._execute(Command.SUBMIT_ELEMENT)

    async def clear(self):
        """Clears the text if it's a text entry element."""
        await self._execute(Command.CLEAR_ELEMENT)

    async def get_property(self, name):
        """ Gets the given property of the element.

        :Args:
            - name - Name of the property to retrieve.

        :Usage:
            ::

                text_length = target_element.get_property("text_length")
        """
        try:
            response = await self._execute(Command.GET_ELEMENT_PROPERTY, {"name": name})
            return response["value"]
        except WebDriverException:
            # if we hit an end point that doesnt understand getElementProperty lets fake it
            response = await self._parent.execute_script('return arguments[0][arguments[1]]', self, name)
            return response

    async def get_attribute(self, name):
        """Gets the given attribute or property of the element.

        This method will first try to return the value of a property with the
        given name. If a property with that name doesn't exist, it returns the
        value of the attribute with the same name. If there's no attribute with
        that name, ``None`` is returned.

        Values which are considered truthy, that is equals "true" or "false",
        are returned as booleans.  All other non-``None`` values are returned
        as strings.  For attributes or properties which do not exist, ``None``
        is returned.

        :Args:
            - name - Name of the attribute/property to retrieve.

        Example::

            # Check if the "active" CSS class is applied to an element.
            is_active = "active" in target_element.get_attribute("class")

        """
        attributeValue = ""
        if self._w3c:
            attributeValue = await self._parent.execute_script(
                f"return ({getAttribute_js}).apply(null, arguments);",
                self, name)
        else:
            response = await self._execute(Command.GET_ELEMENT_ATTRIBUTE, {'name': name})
            attributeValue = response.get('value')
            if attributeValue is not None:
                if name != "value" and attributeValue.lower() in ("true", "false"):
                    attributeValue = attributeValue.lower()
        return attributeValue

    async def is_selected(self):
        """Returns whether the element is selected.

        Can be used to check if a checkbox or radio button is selected.
        """
        respose = await self._execute(Command.IS_ELEMENT_SELECTED)
        return respose['value']

    async def is_enabled(self):
        """Returns whether the element is enabled."""
        respose = await self._execute(Command.IS_ELEMENT_ENABLED)
        return respose['value']

    async def send_keys(self, *value):
        """ Simulates typing into the element.

        :Args:
            - value - A string for typing, or setting form fields.  For setting
              file inputs, this could be a local file path.

        Use this to send simple key events or to fill out form fields::

            form_textfield = driver.find_element(By.NAME, 'username')
            form_textfield.send_keys("admin")

        This can also be used to set file inputs.

        ::

            file_input = driver.find_element(By.NAME, 'profilePic')
            file_input.send_keys("path/to/profilepic.gif")
            # Generally it's better to wrap the file path in one of the methods
            # in os.path to return the actual path to support cross OS testing.
            # file_input.send_keys(os.path.abspath("path/to/profilepic.gif"))

        """
        # transfer file to another machine only if remote driver is used
        # the same behaviour as for java binding
        if self._parent._is_remote:
            local_file = self._parent.file_detector.get_local_filepath(*value)
            if local_file is not None:
                value = await self._upload(local_file)

        await self._execute(Command.SEND_KEYS_TO_ELEMENT,
                      {'text': "".join(keys_to_typing(value)),
                       'value': keys_to_typing(value)})

    # RenderedWebElement Items
    async def is_displayed(self):
        """Whether the element is visible to a user."""
        # Only go into this conditional for browsers that don't use the atom themselves
        if self._w3c:
            response = await self._parent.execute_script(
                f"return ({isDisplayed_js}).apply(null, arguments);",
                self)
            return response
        else:
            response = await self._execute(Command.IS_ELEMENT_DISPLAYED)
            return response['value']

    async def get_screenshot_as_base64(self):
        """ Gets the screenshot of the current element as a base64 encoded string.

        :Usage:
            ::

                img_b64 = element.screenshot_as_base64
        """
        response = await self._execute(Command.ELEMENT_SCREENSHOT)
        return response['value']

    async def get_screenshot_as_png(self):
        """
        Gets the screenshot of the current element as a binary data.

        :Usage:
            ::

                element_png = element.screenshot_as_png
        """
        img_b64 = await self.get_screenshot_as_base64().encode('ascii')
        return base64.b64decode(img_b64)

    async def save_screenshot(self, filename):
        """ Saves a screenshot of the current element to a PNG image file. Returns
           False if there is any IOError, else returns True. Use full paths in
           your filename.

        :Args:
         - filename: The full path you wish to save your screenshot to. This
           should end with a `.png` extension.

        :Usage:
            ::

                element.screenshot('/Screenshots/foo.png')
        """
        if not filename.lower().endswith('.png'):
            warnings.warn("name used for saved screenshot does not match file "
                          "type. It should end with a `.png` extension", UserWarning)
        png_file = await self.get_screenshot_as_png()
        try:
            async with aiofiles.open(filename, mode="wb") as fd:
                await fd.write(png_file)
        except IOError:
            return False
        finally:
            del png_file
        return True
    
    async def find_element(self, by=By.ID, value=None):
        """
        Find an element given a By strategy and locator. Prefer the find_element_by_* methods when
        possible.

        :Usage:
            ::

                element = element.find_element(By.ID, 'foo')

        :rtype: WebElement
        """
        by, value = By.get_w3caware_by_value(by, value, self._w3c)
        response = await self._execute(Command.FIND_CHILD_ELEMENT,
                             {'using': by, 'value': value})
        return response['value']

    async def find_elements(self, by=By.ID, value=None):
        """
        Find elements given a By strategy and locator. Prefer the find_elements_by_* methods when
        possible.

        :Usage:
            ::

                element = element.find_elements(By.CLASS_NAME, 'foo')

        :rtype: list of WebElement
        """
        by, value = By.get_w3caware_by_value(by, value, self._w3c)
        response = await  self._execute(Command.FIND_CHILD_ELEMENTS,
                             {'using': by, 'value': value})
        return response['value']
    
    async def _execute(
        self,
        command,
        params = None):
        """Executes a command against the underlying HTML element.

        Args:
          command: The name of the command to _execute as a string.
          params: A dictionary of named parameters to send with the command.

        Returns:
          The command's JSON response loaded into a dictionary object.
        """
        params = params or {}
        params['id'] = self._id
        response = await self._parent.execute(command, params)
        return response

    async def _upload(self, filename):
        fp = IOStream()
        with zipfile.ZipFile(fp, "w", zipfile.ZIP_DEFLATED) as zipped:
            zipped.write(filename, os.path.split(filename)[-1])
        content = encodebytes(fp.getvalue())
        try:
            response = await self._execute(Command.UPLOAD_FILE, {'file': content})
            return response['value']
        except WebDriverException as ex:
            if "Unrecognized command: POST" in str(ex):
                return filename
            elif "Command not found: POST " in str(ex):
                return filename
            elif '{"status":405,"value":["GET","HEAD","DELETE"]}' in str(ex):
                return filename
            else:
                raise ex
        finally:
            fp.close()
    
    def __eq__(self, element):
        return hasattr(element, "id") and self._id == element.id

    def __ne__(self, element):
        return not self.__eq__(element)
    
    def __hash__(self):
        md5_hash = hashlib.md5(self._id.encode("utf-8")).hexdigest()
        return int(md5_hash, 16)
    
    def __repr__(self):
        return f"<{type(self).__module__}.{type(self).__name__} (session='{self._parent.session_id}', element='{self._id}')>"
