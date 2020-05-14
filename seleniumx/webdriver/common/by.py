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

class By(object):
    """ Set of supported locator strategies. """

    ID = "id"
    XPATH = "xpath"
    LINK_TEXT = "link text"
    PARTIAL_LINK_TEXT = "partial link text"
    NAME = "name"
    TAG_NAME = "tag name"
    CLASS_NAME = "class name"
    CSS_SELECTOR = "css selector"

    @staticmethod
    def get_w3caware_by_value(by, value, w3c_flag):
        if not w3c_flag:
            return (by, value)
        if by == By.ID:
            by = By.CSS_SELECTOR
            value = f'[id="{value}"]'
        elif by == By.TAG_NAME:
            by = By.CSS_SELECTOR
        elif by == By.CLASS_NAME:
            by = By.CSS_SELECTOR
            value = f".{value}"
        elif by == By.NAME:
            by = By.CSS_SELECTOR
            value = f'[name="{value}"]'
        return (by, value)
