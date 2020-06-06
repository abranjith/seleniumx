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


from seleniumx.common.exceptions import WebDriverException

def with_tag_name(tag_name):
    if tag_name is None:
        raise WebDriverException("tag_name can not be null")
    return RelativeBy({'css selector': tag_name})

class RelativeBy(object):

    def __init__(
        self,
        root = None,
        filters = None
    ):
        self.root = root
        self.filters = filters or []

    def above(
        self,
        element_or_locator = None
    ):
        if element_or_locator is None:
            raise WebDriverException("Element or locator must be given when calling above method")
        d = self._get_kind_dict("above", element_or_locator)
        self.filters.append(d)
        return self

    def below(
        self,
        element_or_locator = None
    ):
        if element_or_locator is None:
            raise WebDriverException("Element or locator must be given when calling above method")

        d = self._get_kind_dict("below", element_or_locator)
        self.filters.append(d)
        return self

    def to_left_of(self, element_or_locator=None):
        if element_or_locator is None:
            raise WebDriverException("Element or locator must be given when calling above method")

        d = self._get_kind_dict("left", element_or_locator)    
        self.filters.append(d)
        return self

    def to_right_of(self, element_or_locator):
        if element_or_locator is None:
            raise WebDriverException("Element or locator must be given when calling above method")

        d = self._get_kind_dict("right", element_or_locator)    
        self.filters.append(d)
        return self

    def near(self, element_or_locator_distance=None):
        if element_or_locator_distance is None:
            raise WebDriverException("Element or locator or distance must be given when calling above method")

        d = self._get_kind_dict("near", element_or_locator_distance)    
        self.filters.append(d)
        return self
    
    def _get_kind_dict(self, kind, arg):
        d = {'kind' : kind, 'args' : [arg]}
        return d

    def to_dict(self):
        return {
            'relative': {
                'root': self.root,
                'filters': self.filters
            }
        }
