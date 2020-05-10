from seleniumx.webdriver.common.enums import Command
from seleniumx.webdriver.remote.command_codec import CommandCodec, CommandSpec

class ChromiumCommandCodec(CommandCodec):
    """ This holds mapping between commands and corresponding http method and url specific to Chromium """

    def __init__(self, browser_name, vendor_prefix):
        self.browser_name = browser_name
        self.vendor_prefix = vendor_prefix
        super().__init__()
        self.add_chromium_commands()
    
    def add_chromium_commands(self):
        get = CommandSpec.for_get
        post = CommandSpec.for_post
        commands = {
            Command.LAUNCH_APP : post(self.for_session + "/chromium/launch_app"),
            Command.SET_NETWORK_CONDITIONS : post(self.for_session + "/chromium/network_conditions"),
            Command.GET_NETWORK_CONDITIONS : get(self.for_session + "/chromium/network_conditions"),
            Command.EXECUTE_CDP_COMMAND : post(self.for_session + f"/{self.vendor_prefix}" + "/cdp/execute"),
            Command.GET_SINKS : get(self.for_session + f"/{self.vendor_prefix}" + "/cast/get_sinks"),
            Command.GET_ISSUE_MESSAGE : get(self.for_session + f"/{self.vendor_prefix}" + "/cast/get_issue_message"),
            Command.SET_SINK_TO_USE : post(self.for_session + f"/{self.vendor_prefix}" + "/cast/set_sink_to_use"),
            Command.START_TAB_MIRRORING : post(self.for_session + f"/{self.vendor_prefix}" + "/cast/start_tab_mirroring"),
            Command.STOP_CASTING : post(self.for_session + f"/{self.vendor_prefix}" + "/cast/stop_casting")
        }
        self.add_commands(commands)
    
    