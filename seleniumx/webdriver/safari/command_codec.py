from seleniumx.webdriver.common.enums import Command
from seleniumx.webdriver.remote.command_codec import CommandCodec, CommandSpec

#TODO - see if browser_name is needed in codec

class SafariCommandCodec(CommandCodec):
    """ This holds mapping between commands and corresponding http method and url specific to Safari """

    def __init__(self, browser_name):
        self.browser_name = browser_name
        super().__init__()
        self.add_safari_commands()
    
    def add_safari_commands(self):
        get = CommandSpec.for_get
        post = CommandSpec.for_post
        commands = {
            Command.GET_PERMISSIONS : get(self.for_session + "/apple/permissions"),
            Command.SET_PERMISSIONS : post(self.for_session + "/apple/permissions"),
            Command.ATTACH_DEBUGGER : post(self.for_session + "/apple/attach_debugger")
        }
        self.add_commands(commands)
    
    