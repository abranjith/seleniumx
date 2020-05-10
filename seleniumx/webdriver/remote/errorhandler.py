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

import json

from seleniumx.common.exceptions import UnexpectedAlertPresentException
from seleniumx.webdriver.common.enums import ErrorCode

class ErrorHandler(object):
    """ Handles errors returned by the WebDriver server """
    def handle(
        self,
        response
    ):
        """ Checks that a JSON response from the WebDriver does not have an error.

        :Args:
         - response - The JSON response from the WebDriver server as a dictionary
           object.

        :Raises: If the response contains an error message.
        """
        status = response.get('status', None)
        if status is None or ErrorCode.is_success(status):
            #no error to handle
            return
        
        value = None
        message = response.get('message', "")
        screen = response.get('screen', "")
        if isinstance(status, int) or str(status).strip().isnumeric():
           status, value, message = self._get_status_value_message(response)
        print("error handler status", status)
        exception_class = ErrorCode.get_exception_for_error(status)
        print("error handler exception", exception_class)
        if isinstance(value, str):
            raise exception_class(value)
        
        value = value or {}
        screen = None
        if isinstance(value, dict) and 'screen' in value:
            screen = value['screen']
        stacktrace = None
        st_value = value.get('stackTrace') or value.get('stacktrace')
        stacktrace = self._get_stacktrace(st_value)
        
        if exception_class == UnexpectedAlertPresentException:
            alert_text = None
            if 'data' in value:
                alert_text = value['data'].get('text')
            elif 'alert' in value:
                alert_text = value['alert'].get('text')
            raise exception_class(message, screen, stacktrace, alert_text)
        
        raise exception_class(message, screen, stacktrace)

    def _get_status_value_message(
        self,
        response
    ):
        status = response.get('status', None)
        value_json = response.get('value', None)
        value, message = None, None
        if value_json:
            try:
                value = self._convert_str_to_json(value_json)
                if len(value.keys()) == 1 and 'value' in value:
                    value = value['value']
                status = value.get('error', None)
                if status is None:
                    status = value.get('status')
                    #this doesn't make sense. It's like 3 levels of value. Don't see any mention of such hierarchy in w3c docs
                    message = value.get('message') or value.get('value')
                    if isinstance(message, dict):
                        value = message
                        message = message.get('message')
                else:
                    message = value.get('message', None)
            except ValueError:
                pass
        if not value:
            value = response.get('value', None)
        if (not message) and isinstance(value, dict) and 'message' in value:
            message = value['message']
        return (status, value, message)
    
    def _convert_str_to_json(self, value_json):
        if isinstance(value_json, str):
            try:
                value = json.loads(value_json)
                return value
            except:
                pass
        return value_json
    
    #some parsing around stacktrace in server response
    def _get_stacktrace(
        self,
        response_stacktrace
    ):
        stacktrace = None
        if not response_stacktrace:
            return stacktrace
        if isinstance(response_stacktrace, str):
            stacktrace = response_stacktrace.split('\n')
        else:
            stacktrace = []
            try:
                for frame in response_stacktrace:
                    if not isinstance(frame, dict):
                        continue
                    file_name = frame.get('fileName', "<anonymous>")
                    line_number = frame.get('lineNumber', None)
                    if line_number:
                        file_name = f"{file_name}:{line_number}"

                    class_name = frame.get('className', None)
                    method = frame.get('methodName', "<anonymous>")
                    if class_name:
                        method = f"{class_name}.{method}"
                    message = f"    at {method} ({file_name})"
                    stacktrace.append(message)
            except TypeError:
                pass
        return stacktrace
