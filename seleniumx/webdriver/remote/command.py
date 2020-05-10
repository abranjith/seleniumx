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

class CommandInfo(object):
    """ Represents a command that is essentially used by webdriver client with command name and parameters to use as part of W3C"""

    def __init__(
        self,
        command,
        session_id = None,
        params = None
    ):
        self._command = command
        self._session_id = session_id
        self._params = params or {}
    
    @property
    def command_enum(self):
        return self._command

    @property
    def session_id(self):
        return self._session_id
    
    @property
    def params(self):
        return self._params
    
    #this is essentially session_id + params
    def get_all_params(self):
        session = {"sessionId": self._session_id}
        all_params = self._params.copy()
        all_params.update(session)
        return all_params