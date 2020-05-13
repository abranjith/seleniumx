from seleniumx.common.exceptions import InvalidArgumentException
from seleniumx.webdriver.remote.webelement import WebElement
from seleniumx.webdriver.support.event_firing_webdriver import EventFiringWebElement
from seleniumx.webdriver.common.actions.device import InputDevice
from seleniumx.webdriver.common.actions.input_actions import KeyActionsMixin, PointerActionsMixin
from seleniumx.webdriver.common.actions.interaction import InteractionType, TypingInteraction, Pause

class KeyInput(InputDevice, KeyActionsMixin):
    def __init__(
        self,
        name
    ):
        super().__init__(name)
        self.type = InteractionType.KEY

    def _add_key_down(self, key, add_to_action=True):
        type_action = TypingInteraction(self, "keyDown", key)
        action = type_action.encode()
        return self.dispatch(action, add_to_action=add_to_action)

    def _add_key_up(self, key, add_to_action=True):
        type_action = TypingInteraction(self, "keyUp", key)
        action = type_action.encode()
        return self.dispatch(action, add_to_action=add_to_action)

    def _add_pause(self, pause_duration=0, add_to_action=True):
        pause = Pause(self, pause_duration)
        action = pause.encode()
        return self.dispatch(action, add_to_action=add_to_action)
    
    async def encode(self):
        async for actions in self.iter_actions():
            yield {
                'type': self.type,
                'id': self.name,
                'actions': [action for action in actions]
            }

class PointerInput(InputDevice, PointerActionsMixin):

    DEFAULT_MOVE_DURATION = 250

    def __init__(
        self,
        kind,
        name
    ):
        super().__init__(name)
        if (kind not in InteractionType.POINTER_KINDS):
            raise InvalidArgumentException(f"Invalid PointerInput kind '{kind}'")
        self.type = InteractionType.POINTER
        self.kind = kind
        self.name = name

    def _add_pointer_move(self, origin=None, duration=None, add_to_action=True, x=None, y=None):
        duration = duration or self.DEFAULT_MOVE_DURATION
        action = dict(type="pointerMove", duration=duration)
        action['x'] = x
        action['y'] = y
        if isinstance(origin, (WebElement, EventFiringWebElement)):
            action['origin'] = {'element-6066-11e4-a52e-4f735466cecf': origin.id}
        elif origin is not None:
            action['origin'] = origin
        return self.dispatch(action, add_to_action=add_to_action)

    def _add_pointer_down(self, button, add_to_action=True):
        action = {'type': "pointerDown", 'duration': 0, 'button': button}
        return self.dispatch(action, add_to_action=add_to_action)

    def _add_pointer_up(self, button, add_to_action=True):
        action = {'type': "pointerUp", 'duration': 0, 'button': button}
        return self.dispatch(action, add_to_action=add_to_action)

    def _add_pointer_cancel(self, add_to_action=True):
        action = {'type': "pointerCancel"}
        return self.dispatch(action, add_to_action=add_to_action)

    def _add_pause(self, pause_duration, add_to_action=True):
        action = {'type': "pause", 'duration': int(pause_duration * 1000)}
        return self.dispatch(action, add_to_action=add_to_action)

    async def encode(self):
        async for actions in self.iter_actions():
            yield {
                'type': self.type,
                'parameters': {'pointerType': self.kind},
                'id': self.name,
                'actions': [action for action in actions]
            }
