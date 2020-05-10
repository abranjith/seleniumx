from enum import Enum, unique
from seleniumx.common import exceptions as wd_exceptions

#NOTE - Enum is unhashable

class Command(object):
    """ Defines constants for the standard WebDriver commands.

    While these constants have no meaning in and of themselves, they are
    used to marshal commands through a service that implements WebDriver's
    remote wire protocol:

        https://github.com/SeleniumHQ/selenium/wiki/JsonWireProtocol
    """

    # Keep in sync with org.openqa.selenium.remote.DriverCommand
    NONE = "null"
    STATUS = "status"
    NEW_SESSION = "newSession"
    GET_ALL_SESSIONS = "getAllSessions"
    DELETE_SESSION = "deleteSession"
    NEW_WINDOW = "newWindow"
    CLOSE = "close"
    QUIT = "quit"
    GET = "get"
    GO_BACK = "goBack"
    GO_FORWARD = "goForward"
    REFRESH = "refresh"
    ADD_COOKIE = "addCookie"
    GET_COOKIE = "getCookie"
    GET_ALL_COOKIES = "getCookies"
    DELETE_COOKIE = "deleteCookie"
    DELETE_ALL_COOKIES = "deleteAllCookies"
    FIND_ELEMENT = "findElement"
    FIND_ELEMENTS = "findElements"
    FIND_CHILD_ELEMENT = "findChildElement"
    FIND_CHILD_ELEMENTS = "findChildElements"
    CLEAR_ELEMENT = "clearElement"
    CLICK_ELEMENT = "clickElement"
    SEND_KEYS_TO_ELEMENT = "sendKeysToElement"
    SEND_KEYS_TO_ACTIVE_ELEMENT = "sendKeysToActiveElement"
    SUBMIT_ELEMENT = "submitElement"
    UPLOAD_FILE = "uploadFile"
    GET_CURRENT_WINDOW_HANDLE = "getCurrentWindowHandle"
    W3C_GET_CURRENT_WINDOW_HANDLE = "w3cGetCurrentWindowHandle"
    GET_WINDOW_HANDLES = "getWindowHandles"
    W3C_GET_WINDOW_HANDLES = "w3cGetWindowHandles"
    GET_WINDOW_SIZE = "getWindowSize"
    W3C_GET_WINDOW_SIZE = "w3cGetWindowSize"
    W3C_GET_WINDOW_POSITION = "w3cGetWindowPosition"
    GET_WINDOW_POSITION = "getWindowPosition"
    SET_WINDOW_SIZE = "setWindowSize"
    W3C_SET_WINDOW_SIZE = "w3cSetWindowSize"
    SET_WINDOW_RECT = "setWindowRect"
    GET_WINDOW_RECT = "getWindowRect"
    SET_WINDOW_POSITION = "setWindowPosition"
    W3C_SET_WINDOW_POSITION = "w3cSetWindowPosition"
    SWITCH_TO_WINDOW = "switchToWindow"
    SWITCH_TO_FRAME = "switchToFrame"
    SWITCH_TO_PARENT_FRAME = "switchToParentFrame"
    GET_ACTIVE_ELEMENT = "getActiveElement"
    W3C_GET_ACTIVE_ELEMENT = "w3cGetActiveElement"
    GET_CURRENT_URL = "getCurrentUrl"
    GET_PAGE_SOURCE = "getPageSource"
    GET_TITLE = "getTitle"
    EXECUTE_SCRIPT = "executeScript"
    W3C_EXECUTE_SCRIPT = "w3cExecuteScript"
    W3C_EXECUTE_SCRIPT_ASYNC = "w3cExecuteScriptAsync"
    GET_ELEMENT_TEXT = "getElementText"
    GET_ELEMENT_VALUE = "getElementValue"
    GET_ELEMENT_TAG_NAME = "getElementTagName"
    SET_ELEMENT_SELECTED = "setElementSelected"
    IS_ELEMENT_SELECTED = "isElementSelected"
    IS_ELEMENT_ENABLED = "isElementEnabled"
    IS_ELEMENT_DISPLAYED = "isElementDisplayed"
    GET_ELEMENT_LOCATION = "getElementLocation"
    GET_ELEMENT_LOCATION_ONCE_SCROLLED_INTO_VIEW = "getElementLocationOnceScrolledIntoView"
    GET_ELEMENT_SIZE = "getElementSize"
    GET_ELEMENT_RECT = "getElementRect"
    GET_ELEMENT_ATTRIBUTE = "getElementAttribute"
    GET_ELEMENT_PROPERTY = "getElementProperty"
    GET_ELEMENT_VALUE_OF_CSS_PROPERTY = "getElementValueOfCssProperty"
    SCREENSHOT = "screenshot"
    ELEMENT_SCREENSHOT = "elementScreenshot"
    IMPLICIT_WAIT = "implicitlyWait"
    EXECUTE_ASYNC_SCRIPT = "executeAsyncScript"
    SET_SCRIPT_TIMEOUT = "setScriptTimeout"
    SET_TIMEOUTS = "setTimeouts"
    GET_TIMEOUTS = "getTimeouts"
    MAXIMIZE_WINDOW = "windowMaximize"
    W3C_MAXIMIZE_WINDOW = "w3cMaximizeWindow"
    GET_LOG = "getLog"
    GET_AVAILABLE_LOG_TYPES = "getAvailableLogTypes"
    FULLSCREEN_WINDOW = "fullscreenWindow"
    MINIMIZE_WINDOW = "minimizeWindow"

    # Alerts
    DISMISS_ALERT = "dismissAlert"
    W3C_DISMISS_ALERT = "w3cDismissAlert"
    ACCEPT_ALERT = "acceptAlert"
    W3C_ACCEPT_ALERT = "w3cAcceptAlert"
    SET_ALERT_VALUE = "setAlertValue"
    W3C_SET_ALERT_VALUE = "w3cSetAlertValue"
    GET_ALERT_TEXT = "getAlertText"
    W3C_GET_ALERT_TEXT = "w3cGetAlertText"
    SET_ALERT_CREDENTIALS = "setAlertCredentials"

    # Advanced user interactions
    W3C_ACTIONS = "actions"
    W3C_CLEAR_ACTIONS = "clearActionState"
    CLICK = "mouseClick"
    DOUBLE_CLICK = "mouseDoubleClick"
    MOUSE_DOWN = "mouseButtonDown"
    MOUSE_UP = "mouseButtonUp"
    MOVE_TO = "mouseMoveTo"

    # Screen Orientation
    SET_SCREEN_ORIENTATION = "setScreenOrientation"
    GET_SCREEN_ORIENTATION = "getScreenOrientation"

    # Touch Actions
    SINGLE_TAP = "touchSingleTap"
    TOUCH_DOWN = "touchDown"
    TOUCH_UP = "touchUp"
    TOUCH_MOVE = "touchMove"
    TOUCH_SCROLL = "touchScroll"
    DOUBLE_TAP = "touchDoubleTap"
    LONG_PRESS = "touchLongPress"
    FLICK = "touchFlick"

    # HTML 5
    EXECUTE_SQL = "executeSql"

    GET_LOCATION = "getLocation"
    SET_LOCATION = "setLocation"

    GET_APP_CACHE = "getAppCache"
    GET_APP_CACHE_STATUS = "getAppCacheStatus"
    CLEAR_APP_CACHE = "clearAppCache"

    GET_LOCAL_STORAGE_ITEM = "getLocalStorageItem"
    REMOVE_LOCAL_STORAGE_ITEM = "removeLocalStorageItem"
    GET_LOCAL_STORAGE_KEYS = "getLocalStorageKeys"
    SET_LOCAL_STORAGE_ITEM = "setLocalStorageItem"
    CLEAR_LOCAL_STORAGE = "clearLocalStorage"
    GET_LOCAL_STORAGE_SIZE = "getLocalStorageSize"

    GET_SESSION_STORAGE_ITEM = "getSessionStorageItem"
    REMOVE_SESSION_STORAGE_ITEM = "removeSessionStorageItem"
    GET_SESSION_STORAGE_KEYS = "getSessionStorageKeys"
    SET_SESSION_STORAGE_ITEM = "setSessionStorageItem"
    CLEAR_SESSION_STORAGE = "clearSessionStorage"
    GET_SESSION_STORAGE_SIZE = "getSessionStorageSize"

    # Mobile
    GET_NETWORK_CONNECTION = "getNetworkConnection"
    SET_NETWORK_CONNECTION = "setNetworkConnection"
    CURRENT_CONTEXT_HANDLE = "getCurrentContextHandle"
    CONTEXT_HANDLES = "getContextHandles"
    SWITCH_TO_CONTEXT = "switchToContext"

    #Chromium
    LAUNCH_APP = "launchApp"
    SET_NETWORK_CONDITIONS = "setNetworkConditions"
    GET_NETWORK_CONDITIONS = "getNetworkConditions"
    EXECUTE_CDP_COMMAND = "executeCdpCommand"
    GET_SINKS = "getSinks"
    GET_ISSUE_MESSAGE = "getIssueMessage"
    SET_SINK_TO_USE = "setSinkToUse"
    START_TAB_MIRRORING = "startTabMirroring"
    STOP_CASTING = "stopCasting"
    
@unique
class HttpMethod(Enum):
    
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    DELETE = "DELETE"

    #string compare with name (case insensitive)
    def __eq__(self, other):
        if isinstance(other, str):
            if str(self.value).lower() == other.strip().lower():
                return True
            return False
        return super().__eq__(other)
    
    def __ne__(self, other):
        return not self.__eq__(other)


class WebDriverError(object):
    """ Every row on this table should be self-explanatory, except for the two booleans at the end.
    The first of these is "is_canonical_json_code" - This means that when doing the mapping
    for a JSON Wire Protocol status code, this WebDriverError provides the exception that should be
    thrown. The second boolean is "is_canonical_w3c" - This means that when mapping a state or
    exception to a W3C state, this WebDriverError provides the default exception and Json Wire Protocol
    status to send (from java docs)
    """
    DEFAULT_EXCEPTION = wd_exceptions.WebDriverException

    def __init__(
        self,
        name,
        json_code,
        w3c_status,
        http_status_code,
        exception,
        is_canonical_json_code = True,
        is_canonical_w3c = True
    ):
        self._name = name
        self._json_code = json_code
        self._w3c_status = w3c_status
        self._http_status_code = http_status_code
        self._exception = exception
        self._is_canonical_json_code = is_canonical_json_code
        self._is_canonical_w3c = is_canonical_w3c
    
    @property
    def name(self):
        return self._name
    
    @property
    def json_code(self):
        return self._json_code

    @property
    def w3c_status(self):
        return self._w3c_status
    
    @property
    def http_status_code(self):
        return self._http_status_code
    
    @property
    def exception(self):
        return self._exception
    
    @property
    def is_canonical_for_w3c(self):
        return self._is_canonical_w3c

    #matches first json code and then w3c status    
    def get_exception_for_value(
        self,
        value
    ):
        if (value == self._json_code or value == self._w3c_status) and self._is_canonical_w3c:
            return self._exception
        return None
    
    def is_match(
        self,
        value
    ):
        if (value == self._json_code or value == self._w3c_status) and self._is_canonical_w3c:
            return True
        return False

@unique
class ErrorCode(Enum):
    """ Error codes defined in the WebDriver wire protocol. 
    NOTE - Keep in sync with org.openqa.selenium.remote.ErrorCodes and errorcodes.h
    """
    SUCCESS = WebDriverError("success", 7, "success", 200, None)
    NO_SUCH_SESSION = WebDriverError("NoSuchSession", 7, "invalid session id", 404, wd_exceptions.NoSuchSessionException)
    NO_SUCH_ELEMENT = WebDriverError("NoSuchElement", 7, "no such element", 404, wd_exceptions.NoSuchElementException)
    NO_SUCH_FRAME = WebDriverError("NoSuchFrame", 8, "no such frame", 404, wd_exceptions.NoSuchFrameException)
    UNKNOWN_COMMAND = WebDriverError("UnknownCommand", 9, "unknown command", 404, wd_exceptions.UnsupportedCommandException)
    STALE_ELEMENT_REFERENCE = WebDriverError("StaleElement", 10, "stale element reference", 404, wd_exceptions.StaleElementReferenceException)
    ELEMENT_NOT_VISIBLE = WebDriverError("ElementNotVisible", 11, "element not visible", 400, wd_exceptions.ElementNotVisibleException)
    INVALID_ELEMENT_STATE = WebDriverError("InvalidElementState", 12, "invalid element state", 400, wd_exceptions.InvalidElementStateException)
    UNKNOWN_ERROR = WebDriverError("UnknownError", 13, "unknown error", 500, wd_exceptions.WebDriverException)
    ELEMENT_NOT_SELECTABLE = WebDriverError("ElementNotSelectable", 15, "element not selectable", 400, wd_exceptions.ElementNotSelectableException)
    JAVASCRIPT_ERROR = WebDriverError("JavascriptError", 17, "javascript error", 500, wd_exceptions.JavascriptException)
    XPATH_LOOKUP_ERROR = WebDriverError("XpathLookup", 19, "invalid selector", 400, wd_exceptions.InvalidSelectorException, is_canonical_json_code=False, is_canonical_w3c=False)
    TIMEOUT = WebDriverError("Timeout", 21, "timeout", 500, wd_exceptions.TimeoutException)
    NO_SUCH_WINDOW = WebDriverError("NoSuchWindow", 23, "no such window", 404, wd_exceptions.NoSuchWindowException)
    INVALID_COOKIE_DOMAIN = WebDriverError("InvalidCookieDomain", 24, "invalid cookie domain", 400, wd_exceptions.InvalidCookieDomainException)
    UNABLE_TO_SET_COOKIE = WebDriverError("UnableToSetCookie", 25, "unable to set cookie", 500, wd_exceptions.UnableToSetCookieException)
    UNEXPECTED_ALERT_OPEN = WebDriverError("UnhandledAlertOpen", 26, "unexpected alert open", 500, wd_exceptions.UnhandledAlertException)
    NO_ALERT_OPEN = WebDriverError("NoAlertPresent", 27, "no such alert", 404, wd_exceptions.NoAlertPresentException)
    SCRIPT_TIMEOUT = WebDriverError("ScriptTimeout", 28, "script timeout", 500, wd_exceptions.ScriptTimeoutException)
    INVALID_ELEMENT_COORDINATES = WebDriverError("InvalidElementCoordinates", 29, "invalid element coordinates", 400, wd_exceptions.InvalidCoordinatesException)
    #TODO - not sure these ime w3c exception messages are correct as java code has something else
    IME_NOT_AVAILABLE = WebDriverError("ImeNotAvailable", 30, "ime not available", 500, wd_exceptions.ImeNotAvailableException, is_canonical_w3c=False)
    IME_ENGINE_ACTIVATION_FAILED = WebDriverError("ImeActivationFailed", 31, "ime engine activation failed", 500, wd_exceptions.ImeActivationFailedException, is_canonical_w3c=False)
    INVALID_SELECTOR = WebDriverError("InvalidSelector", 32, "invalid selector", 400, wd_exceptions.InvalidSelectorException)
    SESSION_NOT_CREATED = WebDriverError("SessioNotCreated", 33, "session not created", 500, wd_exceptions.SessionNotCreatedException)
    MOVE_TARGET_OUT_OF_BOUNDS = WebDriverError("MoveTargetOutOfBounds", 34, "move target out of bounds", 500, wd_exceptions.MoveTargetOutOfBoundsException)
    INVALID_XPATH_SELECTOR = WebDriverError("InvalidXpathSelector", 51, "invalid selector", 400, wd_exceptions.InvalidSelectorException, is_canonical_json_code=False, is_canonical_w3c=False)
    INVALID_XPATH_SELECTOR_RETURN_TYPER = WebDriverError("InvalidXpathReturnType", 52, "invalid selector", 400, wd_exceptions.InvalidSelectorException, is_canonical_json_code=False)

    #json wire protocol doesn't have analogous status codes for these new W3C status response 'codes', so making some up! (from java docs)
    ELEMENT_NOT_INTERACTABLE = WebDriverError("ElementNotInteractable", 60, "element not interactable", 400, wd_exceptions.ElementNotInteractableException)
    INVALID_ARGUMENT = WebDriverError("InvalidArgument", 61, "invalid argument", 400, wd_exceptions.InvalidArgumentException)
    NO_SUCH_COOKIE = WebDriverError("NoSuchCookie", 62, "no such cookie", 404, wd_exceptions.NoSuchCookieException)
    UNABLE_TO_CAPTURE_SCREEN = WebDriverError("Screenshot", 63, "unable to capture screen", 500, wd_exceptions.ScreenshotException)
    ELEMENT_CLICK_INTERCEPTED = WebDriverError("ElementClickIntercepted", 64, "element click intercepted", 400, wd_exceptions.ElementClickInterceptedException)

    METHOD_NOT_ALLOWED = WebDriverError("MethodNotAllowed", 405, "unsupported operation", 500, wd_exceptions.UnsupportedCommandException, is_canonical_json_code=False)
    UNKNOWN_METHOD = WebDriverError("UnknownMethod", 405, "unknown method", 405, wd_exceptions.UnsupportedCommandException, is_canonical_json_code=False)

    #json codes not known (couldn't find in java docs)
    INSECURE_CERTIFICATE = WebDriverError("InsecureCertificate", -1, "insecure certificate", 500, wd_exceptions.InsecureCertificateException)
    INVALID_SESSION_ID = WebDriverError("InvalidSessionId", -1, "invalid session id", 500, wd_exceptions.InvalidSessionIdException)
    INVALID_COORDINATES = WebDriverError("InvalidCoordinates", -1, "invalid coordinates", 500, wd_exceptions.InvalidCoordinatesException)

    @staticmethod
    def get_exception_for_error(error):
        for _, v in ErrorCode.__members__.items():
            wd_error = v.value
            if wd_error.is_match(error):
                return wd_error.exception
        return WebDriverError.DEFAULT_EXCEPTION
    
    @staticmethod
    def is_success(code):
        wd_success = ErrorCode.SUCCESS.value
        if wd_success.is_match(code):
            return True
        return False
