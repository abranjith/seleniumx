from seleniumx.webdriver.common.enums import Command
from seleniumx.webdriver.remote.command_codec import CommandCodec, CommandSpec

class FirefoxCommandCodec(CommandCodec):
    """ This holds mapping between commands and corresponding http method and url specific to Chromium """

    def __init__(self, browser_name):
        self.browser_name = browser_name
        super().__init__()
        self.add_firefox_commands()
    
    def add_firefox_commands(self):
        get = CommandSpec.for_get
        post = CommandSpec.for_post
        commands = {
            Command.GET_CONTEXT : get(self.for_session + "/moz/context"),
            Command.SET_CONTEXT : post(self.for_session + "/moz/context"),
            Command.ELEMENT_GET_ANONYMOUS_CHILDREN : post(self.for_session + "/moz/xbl/{id}/anonymous_children"),
            Command.ELEMENT_FIND_ANONYMOUS_ELEMENTS_BY_ATTRIBUTE : post(self.for_session + "/moz/xbl/{id}/anonymous_by_attribute"),
            Command.INSTALL_ADDON : post(self.for_session + "/moz/addon/install"),
            Command.UNINSTALL_ADDON : post(self.for_session + "/moz/addon/uninstall"),
            Command.FULL_PAGE_SCREENSHOT : get(self.for_session + "/moz/screenshot/full")
        }
        self.add_commands(commands)
    
    