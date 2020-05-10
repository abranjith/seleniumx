from seleniumx.webdriver.common.enums import HttpMethod, Command
from seleniumx.webdriver.remote.command import CommandInfo

class CommandCodec(object):
    """ This holds mapping between commands and corresponding http method and url. Some of the design inspirations are taken from java counterpart
    NOTE - whenever there is an update on command, this class needs to be kept up to date. See https://w3c.github.io/webdriver/#endpoints for details
    """
    browser_name = None

    def __init__(self):
        #holds mapping between command and the spec info (http method and path)
        self._commands = {}
        #command aliases
        self._aliases = {}
        self.for_session = r"/session/{sessionId}"
        self.for_element = self.for_session + r"/element/{id}"
        self.for_windowhandle = self.for_session + r"/window/{windowHandle}"
        self._init_command_specs()
    
    def _init_command_specs(self):
        get = CommandSpec.for_get
        post = CommandSpec.for_post
        delete = CommandSpec.for_delete
        
        self._commands = {
            Command.STATUS: get("/status"),
            Command.NEW_SESSION: post("/session"),
            Command.GET_ALL_SESSIONS: get("/sessions"),
            
            #these are performed on established session
            Command.QUIT: delete(self.for_session),
            Command.GET_CURRENT_WINDOW_HANDLE: get(self.for_session + "/window_handle"),
            Command.W3C_GET_CURRENT_WINDOW_HANDLE: get(self.for_session + "/window"),
            Command.GET_WINDOW_HANDLES: get(self.for_session + "/window_handles"),
            Command.W3C_GET_WINDOW_HANDLES: get( self.for_session + "/window/handles"),
            Command.GET: post(self.for_session + "/url"),
            Command.GO_FORWARD: post(self.for_session + "/forward"),
            Command.GO_BACK: post(self.for_session + "/back"),
            Command.REFRESH: post(self.for_session + "/refresh"),
            Command.EXECUTE_SCRIPT: post(self.for_session + "/execute"),
            Command.W3C_EXECUTE_SCRIPT: post(self.for_session + "/execute/sync"),
            Command.W3C_EXECUTE_SCRIPT_ASYNC: post(self.for_session + "/execute/async"),
            Command.GET_CURRENT_URL: get(self.for_session + "/url"),
            Command.GET_TITLE: get(self.for_session +  "/title"),
            Command.GET_PAGE_SOURCE: get(self.for_session +  "/source"),
            Command.SCREENSHOT: get(self.for_session +  "/screenshot"),
            Command.FIND_ELEMENT: post(self.for_session +  "/element"),
            Command.FIND_ELEMENTS: post(self.for_session +  "/elements"),
            Command.W3C_GET_ACTIVE_ELEMENT: get(self.for_session +  "/element/active"),
            Command.GET_ACTIVE_ELEMENT: post(self.for_session +  "/element/active"),
            Command.GET_ALL_COOKIES: get(self.for_session +  "/cookie"),
            Command.ADD_COOKIE: post(self.for_session +  "/cookie"),
            Command.GET_COOKIE: get(self.for_session +  r"/cookie/{name}"),
            Command.DELETE_ALL_COOKIES: delete(self.for_session +  "/cookie"),
            Command.DELETE_COOKIE: delete(self.for_session +  r"/cookie/{name}"),
            Command.SWITCH_TO_FRAME: post(self.for_session +  "/frame"),
            Command.SWITCH_TO_PARENT_FRAME: post(self.for_session +  "/frame/parent"),
            Command.SWITCH_TO_WINDOW: post(self.for_session +  "/window"),
            Command.NEW_WINDOW: post(self.for_session +  "/window/new"),
            Command.CLOSE: delete(self.for_session +  "/window"),

            #these are performed on identified element
            Command.ELEMENT_SCREENSHOT: get(self.for_element + "/screenshot"),
            Command.FIND_CHILD_ELEMENT: post(self.for_element + "/element"),
            Command.FIND_CHILD_ELEMENTS: post(self.for_element + "/elements"),
            Command.CLICK_ELEMENT: post(self.for_element + "/click"),
            Command.CLEAR_ELEMENT: post(self.for_element + "/clear"),
            Command.SUBMIT_ELEMENT: post(self.for_element + "/submit"),
            Command.GET_ELEMENT_TEXT: get(self.for_element + "/text"),
            Command.SEND_KEYS_TO_ELEMENT: post(self.for_element + "/value"),
            Command.SEND_KEYS_TO_ACTIVE_ELEMENT: post(self.for_session +  "/keys"),
            Command.UPLOAD_FILE: post(self.for_session + "/file"),
            Command.GET_ELEMENT_VALUE: get(self.for_element + "/value"),
            Command.GET_ELEMENT_TAG_NAME: get(self.for_element + "/name"),
            Command.IS_ELEMENT_SELECTED: get(self.for_element + "/selected"),
            Command.SET_ELEMENT_SELECTED: post(self.for_element + "/selected"),
            Command.IS_ELEMENT_ENABLED: get(self.for_element + "/enabled"),
            Command.IS_ELEMENT_DISPLAYED: get(self.for_element + "/displayed"),
            Command.GET_ELEMENT_LOCATION: get(self.for_element + "/location"),
            Command.GET_ELEMENT_LOCATION_ONCE_SCROLLED_INTO_VIEW: get(self.for_element + "/location_in_view"),
            Command.GET_ELEMENT_SIZE: get(self.for_element + "/size"),
            Command.GET_ELEMENT_RECT: get(self.for_element + "/rect"),
            Command.GET_ELEMENT_ATTRIBUTE: get(self.for_element + r"/attribute/{name}"),
            Command.GET_ELEMENT_PROPERTY: get(self.for_element + r"/property/{name}"),
            Command.GET_ELEMENT_VALUE_OF_CSS_PROPERTY: get(self.for_element + r"/css/{propertyName}"),
            
            Command.IMPLICIT_WAIT: post(self.for_session +  "/timeouts/implicit_wait"),
            Command.EXECUTE_ASYNC_SCRIPT: post(self.for_session +  "/execute_async"),
            Command.SET_SCRIPT_TIMEOUT: post(self.for_session +  "/timeouts/async_script"),
            Command.SET_TIMEOUTS: post(self.for_session +  "/timeouts"),
            Command.GET_TIMEOUTS: get(self.for_session +  "/timeouts"),

            Command.DISMISS_ALERT: post(self.for_session +  "/dismiss_alert"),
            Command.W3C_DISMISS_ALERT: post(self.for_session +  "/alert/dismiss"),
            Command.ACCEPT_ALERT: post(self.for_session +  "/accept_alert"),
            Command.W3C_ACCEPT_ALERT: post(self.for_session +  "/alert/accept"),
            Command.SET_ALERT_VALUE: post(self.for_session +  "/alert_text"),
            Command.W3C_SET_ALERT_VALUE: post(self.for_session +  "/alert/text"),
            Command.GET_ALERT_TEXT: get(self.for_session +  "/alert_text"),
            Command.W3C_GET_ALERT_TEXT: get(self.for_session +  "/alert/text"),
            Command.SET_ALERT_CREDENTIALS: post(self.for_session +  "/alert/credentials"),
            
            Command.CLICK: post(self.for_session +  "/click"),
            Command.W3C_ACTIONS: post(self.for_session +  "/actions"),
            Command.W3C_CLEAR_ACTIONS: delete(self.for_session +  "/actions"),
            Command.DOUBLE_CLICK: post(self.for_session +  "/doubleclick"),
            Command.MOUSE_DOWN: post(self.for_session +  "/buttondown"),
            Command.MOUSE_UP: post(self.for_session +  "/buttonup"),
            Command.MOVE_TO: post(self.for_session +  "/moveto"),
            
            Command.GET_WINDOW_SIZE: get(self.for_windowhandle + "/size"),
            Command.SET_WINDOW_SIZE: post(self.for_windowhandle + "/size"),
            Command.GET_WINDOW_POSITION: get(self.for_windowhandle + "/position"),
            Command.SET_WINDOW_POSITION: post(self.for_windowhandle + "/position"),
            Command.MAXIMIZE_WINDOW: post(self.for_windowhandle + "/maximize"),
            Command.SET_WINDOW_RECT: post(self.for_session +  "/window/rect"),
            Command.GET_WINDOW_RECT: get(self.for_session +  "/window/rect"),
            Command.W3C_MAXIMIZE_WINDOW: post(self.for_session +  "/window/maximize"),
            
            Command.SET_SCREEN_ORIENTATION: post(self.for_session +  "/orientation"),
            Command.GET_SCREEN_ORIENTATION: get(self.for_session +  "/orientation"),
            
            Command.SINGLE_TAP: post(self.for_session +  "/touch/click"),
            Command.TOUCH_DOWN: post(self.for_session +  "/touch/down"),
            Command.TOUCH_UP: post(self.for_session +  "/touch/up"),
            Command.TOUCH_MOVE: post(self.for_session +  "/touch/move"),
            Command.TOUCH_SCROLL: post(self.for_session +  "/touch/scroll"),
            Command.DOUBLE_TAP: post(self.for_session +  "/touch/doubleclick"),
            Command.LONG_PRESS: post(self.for_session +  "/touch/longclick"),
            Command.FLICK: post(self.for_session +  "/touch/flick"),
            
            Command.EXECUTE_SQL: post(self.for_session +  "/execute_sql"),
            Command.GET_LOCATION: get(self.for_session +  "/location"),
            Command.SET_LOCATION: post(self.for_session +  "/location"),
            Command.GET_APP_CACHE: get(self.for_session +  "/application_cache"),
            Command.GET_APP_CACHE_STATUS: get(self.for_session +  "/application_cache/status"),
            Command.CLEAR_APP_CACHE: delete(self.for_session +  "/application_cache/clear"),
            Command.GET_NETWORK_CONNECTION: get(self.for_session +  "/network_connection"),
            Command.SET_NETWORK_CONNECTION: post(self.for_session +  "/network_connection"),
            Command.GET_LOCAL_STORAGE_ITEM: get(self.for_session +  r"/local_storage/key/{key}"),
            Command.REMOVE_LOCAL_STORAGE_ITEM: delete(self.for_session +  r"/local_storage/key/{key}"),
            Command.GET_LOCAL_STORAGE_KEYS: get(self.for_session +  "/local_storage"),
            Command.SET_LOCAL_STORAGE_ITEM: post(self.for_session +  "/local_storage"),
            Command.CLEAR_LOCAL_STORAGE: delete(self.for_session +  "/local_storage"),
            Command.GET_LOCAL_STORAGE_SIZE: get(self.for_session +  "/local_storage/size"),
            Command.GET_SESSION_STORAGE_ITEM: get(self.for_session +  r"/session_storage/key/{key}"),
            Command.REMOVE_SESSION_STORAGE_ITEM: delete(self.for_session +  r"/session_storage/key/{key}"),
            Command.GET_SESSION_STORAGE_KEYS: get(self.for_session +  "/session_storage"),
            Command.SET_SESSION_STORAGE_ITEM: post(self.for_session +  "/session_storage"),
            Command.CLEAR_SESSION_STORAGE: delete(self.for_session +  "/session_storage"),
            Command.GET_SESSION_STORAGE_SIZE: get(self.for_session +  "/session_storage/size"),
            
            Command.GET_LOG: post(self.for_session +  "/se/log"),
            Command.GET_AVAILABLE_LOG_TYPES: get(self.for_session +  "/se/log/types"),
            Command.CURRENT_CONTEXT_HANDLE: get(self.for_session +  "/context"),
            Command.CONTEXT_HANDLES: get(self.for_session +  "/contexts"),
            Command.SWITCH_TO_CONTEXT: post(self.for_session +  "/context"),
            Command.FULLSCREEN_WINDOW: post(self.for_session +  "/window/fullscreen"),
            Command.MINIMIZE_WINDOW: post(self.for_session +  "/window/minimize")
        }

    def add_command(
        self,
        command : Command,
        http_method : HttpMethod,
        url_path : str
    ):
        if not isinstance(command, Command):
            raise ValueError(f"{command} need to be valid Command type")
        cmd_spec = CommandSpec(http_method, url_path)
        self._commands[command] = cmd_spec
    
    def add_commands(
        self,
        commands : dict
    ):
        if commands:
            self._commands.update(commands)

    def add_alias(
        self,
        command : Command, 
        alias_for_command: Command):
        if (isinstance(command, Command) and isinstance(alias_for_command, Command)):
            self._aliases[command] = alias_for_command
        else:
            raise ValueError(f"{command} and {alias_for_command} both need to be valid Command types")
    
    def _build_url(
        self,
        url_path : str,
        params : dict
    ):
        updated_url_path = None
        try:
            updated_url_path = str(url_path).format(**params)
        except KeyError as ex:
            raise ValueError(f"{str(ex)} is a required placeholder in url that is not provided")
        return updated_url_path

    def encode(
        self,
        command : CommandInfo
    ):
        if not isinstance(command, CommandInfo):
            raise ValueError("command must be valid and of type CommandInfo")
        command_enum = command.command_enum
        command_enum = self._aliases.get(command_enum, command_enum)
        if not self._commands.get(command_enum):
            raise ValueError(f"{command_enum} is not recognized as a valid command")
        command_spec = self._commands[command_enum]
        updated_url_path = self._build_url(command_spec.url_path, command.get_all_params())
        return ParsedCommandSpec(command_spec.http_method, updated_url_path)

class CommandSpec(object):

    def __init__(
        self,
        http_method : HttpMethod,
        url_path : str
    ):
        self._http_method = http_method
        self._url_path = url_path

    @staticmethod
    def for_get(url_path):
        return CommandSpec(HttpMethod.GET, url_path)
    
    @staticmethod
    def for_post(url_path):
        return CommandSpec(HttpMethod.POST, url_path)
    
    @staticmethod
    def for_delete(url_path):
        return CommandSpec(HttpMethod.DELETE, url_path)
    
    @property
    def http_method(self):
        return self._http_method
    
    @property
    def url_path(self):
        return self._url_path
    
    def __str__(self):
        return f"<{self.http_method.value} - {self.url_path}>"

ParsedCommandSpec = CommandSpec
