import platform
import base64
import json
from urllib.parse import urlparse, urljoin

from seleniumx import __version__
from seleniumx.webdriver.common.enums import ErrorCode
from seleniumx.webdriver.common.http_client import HttpClient
from seleniumx.webdriver.remote.command import CommandInfo
from seleniumx.webdriver.remote.command_codec import CommandCodec, Command
from seleniumx.webdriver.remote.errorhandler import ErrorHandler

class HttpExecutor(object):
    """ Takes care of making http calls and getting response that is understood by WebDriver """
    def __init__(
        self,
        webdriver_instance,
        command_codec : CommandCodec,
        base_url = None,
        keep_alive = True,
        timeout = None,
        ca_certs = None,
        headers = None
    ):
        self._webdriver = webdriver_instance
        self._base_url = base_url
        self._keep_alive = keep_alive
        self._timeout = timeout
        self._ca_certs = ca_certs
        self._command_codec = command_codec
        self._headers = self._get_default_headers(headers)
        self._w3c = False
        self._request_wrapper = WebDriverRequestWrapper()
        self._response_wrapper = WebDriverResponseWrapper()
        self._http_client = HttpClient(base_url=self._base_url, keep_alive=self._keep_alive, timeout=self._timeout, cert=self._ca_certs)
    
    @property
    def w3c(self):
        return self._w3c
    
    @w3c.setter
    def w3c(self, value):
        if value is not None:
            self._w3c = value
    
    @property
    def base_url(self):
        return self._base_url
    
    @base_url.setter
    def base_url(self, url):
        if url is not None:
            self._base_url = url
            self._http_client.base_url = url

    def _get_default_headers(self, additional_headers=None):
        system = platform.system().lower()
        system = "mac" if system == "darwin" else system

        headers = {
            'Accept': "application/json",
            'Content-Type': "application/json;charset=UTF-8",
            'User-Agent': f"selenium/{__version__} (python {system})"
        }
        if self._keep_alive:
            headers['Connection'] = "keep-alive"
        
        if additional_headers:
            headers.update(additional_headers)

        return headers
    
    def _get_basic_auth_for_url(self, url_path):
        full_url = urljoin(self._base_url, url_path)
        url_parts = urlparse(full_url)
        if url_parts.username:
            base64string = base64.b64encode(f"{url_parts.username}:{url_parts.password}".encode())
            return f"Basic {base64string.decode()}"
    
    def _update_header_for_auth(self, url_path):
        basic_auth = self._get_basic_auth_for_url(url_path)
        if basic_auth:
            self._headers['Authorization'] = basic_auth
    
    async def execute(
        self,
        command_enum : Command,
        session_id,
        params
    ):
        params = params or {}
        #don't want to alter what caller has sent
        params = params.copy()
        if self._w3c and "sessionId" in params:
            del params["sessionId"]
        params = self._request_wrapper.unwrap_web_element(params)
        #construct command object
        command = CommandInfo(command_enum, session_id=session_id, params=params)
        remote_response = None
        try:
            #get updated url path & http method
            parsed_command_spec = self._command_codec.encode(command)
            self._update_header_for_auth(parsed_command_spec.url_path)
            #params being passed as payload might be a bit confusing. This is partly because of webdriver protocol specs.
            #Apparently all the params used in url path are also part of body (with the exception of sessionId as far as I can tell)
            remote_response = await self._http_client.request(parsed_command_spec.http_method, parsed_command_spec.url_path, payload=params, headers=self._headers)
            response = await self._response_wrapper.create_response(remote_response)
        except Exception as ex:
            response = self._response_wrapper.create_response_for_error(str(ex), ex)
        finally:
            if remote_response and hasattr(remote_response, "aclose"):
                await remote_response.aclose()
                remote_response = None
        #in case of error handle accordingly
        #print(remote_response)
        error_handler = ErrorHandler()
        error_handler.handle(response)
        #wrap the webelements
        response = self._response_wrapper.wrap_web_element(self._webdriver, response, self._w3c)
        return response
    
    #closes any underlying connections & pools
    async def close(self):
        if self._http_client:
            await self._http_client.close()

class WebDriverWrapper(object):
    from seleniumx.webdriver.remote.webelement import WebElement
    _web_element_cls = WebElement
    #per webdriver specs remote server recognizes web element by id that's associated with either of below keys
    ELEMENT1 = "ELEMENT"
    ELEMENT2 = "element-6066-11e4-a52e-4f735466cecf"
    #represents an error response (from w3c docs - https://w3c.github.io/webdriver/#errors)
    _ERROR_OBJ_TEMPLATE = {
        'status' : None, 
        'value' : {
            'error' : None,
            'message' : None,
            'stacktrace' : None
            }
        }
    
    def get_error_template(self):
        return self._ERROR_OBJ_TEMPLATE.copy()

class WebDriverRequestWrapper(WebDriverWrapper):

    def unwrap_web_element(self, value):
        """ Unwraps a WebElement object to w3c compatible element id """
        if isinstance(value, dict):
            converted = {}
            for k, v in value.items():
                converted[k] = self.unwrap_web_element(v)
            return converted
        elif isinstance(value, self._web_element_cls):
            return {self.ELEMENT1: value.id, self.ELEMENT2: value.id}
        elif isinstance(value, list):
            return list(self.unwrap_web_element(item) for item in value)
        else:
            return value

class WebDriverResponseWrapper(WebDriverWrapper):

    def create_web_element(self, webdriver, element_id, is_w3c):
        """Creates a web element with the specified `element_id`."""
        return self._web_element_cls(webdriver, element_id, w3c=is_w3c)

    def wrap_web_element(self, webdriver, value, is_w3c):
        """ Wraps a w3c element id into WebElement object """
        if isinstance(value, dict):
            if self.ELEMENT1 in value or self.ELEMENT2 in value:
                if value.get(self.ELEMENT1, None) is not None:
                    return self.create_web_element(webdriver, value[self.ELEMENT1], is_w3c)
                else:
                    return self.create_web_element(webdriver, value[self.ELEMENT2], is_w3c)
            else:
                converted = {}
                for k, v in value.items():
                    converted[k] = self.wrap_web_element(webdriver, v, is_w3c)
                return converted
        elif isinstance(value, list):
            return list(self.wrap_web_element(webdriver, item, is_w3c) for item in value)
        else:
            return value
        
    async def create_response(self, response):
        #believe this is the right thing to do
        if not response:
            raise ValueError("Invalid response received from remote server")
        response_bytes = await response.aread()
        response_bytes = response_bytes or b""
        is_json = False
        #older implementation checks for image. Don't believe that is necessary. Not sure what scenario causes server to send image
        try:
            #get text
            response_data = response_bytes.decode(response.encoding, errors="replace")
            #if it is json, use json
            response_data = json.loads(response_data)
            is_json = True
        except:
            pass    
        
        if response.is_error:
            return {'status': response.status_code, 'value': response_data}

        #in case of valid json response, return the same
        if is_json:
            #apparently value is expected in remote response, but not all drivers necessarily send value
            if 'value' not in response_data:
                response_data['value'] = None
            return response_data
        #success, but probably not w3c compliant
        status_obj = ErrorCode.SUCCESS.value
        resp = {'status': status_obj.json_code, 'value': response_data}
        return resp
    
    def create_response_for_error(self, message, stacktrace=None):
        error_obj = self.get_error_template()
        error_code = ErrorCode.UNKNOWN_ERROR.value
        error_obj['status'] = error_code.json_code
        error_obj['value']['error'] = error_code.w3c_status
        error_obj['value']['message'] = message
        error_obj['value']['stacktrace'] = stacktrace
        return error_obj