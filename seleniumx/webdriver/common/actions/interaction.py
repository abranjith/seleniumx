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


class InteractionType(object):

    KEY = "key"
    POINTER = "pointer"
    NONE = "none"
    SOURCE_TYPES = set([KEY, POINTER, NONE])

    POINTER_MOUSE = "mouse"
    POINTER_TOUCH = "touch"
    POINTER_PEN = "pen"

    POINTER_KINDS = set([POINTER_MOUSE, POINTER_TOUCH, POINTER_PEN])

class MouseButton(object):

    LEFT = 0
    MIDDLE = 1
    RIGHT = 2


class Interaction(object):
    
    def __init__(
        self,
        source
    ):
        self.source = source

class Pause(Interaction):
    
    PAUSE = "pause"

    def __init__(
        self,
        source,
        duration = 0
    ):
        super().__init__(source)
        self.duration = duration

    def encode(self):
        return {'type': self.PAUSE, 'duration': int(self.duration * 1000)}

class TypingInteraction(Interaction):

    def __init__(
        self,
        source,
        type_,
        key
    ):
        super().__init__(source)
        self.type = type_
        self.key = key

    def encode(self):
        return {'type': self.type, 'value': self.key}
