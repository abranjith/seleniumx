from seleniumx.webdriver.remote.webelement import WebElement
from seleniumx.webdriver.support.event_firing_webdriver import EventFiringWebElement
from seleniumx.webdriver.common.utils import keys_to_typing
from seleniumx.webdriver.common.actions.interaction import MouseButton, InteractionType, Interaction
from seleniumx.webdriver.common.actions.device import Action

class KeyActionsMixin(Interaction):
    """ This class is not supposed to be used on its own, but as a Mixin with KeyInput class """
   
    def __init__(self):
        super().__init__(self)

    def key_down(self, letter):
        self._add_key_down(letter)      # pylint: disable=no-member
        return self

    def key_up(self, letter):
        self._add_key_up(letter)      # pylint: disable=no-member
        return self

    def pause(self, duration=0):
        self._add_pause(duration)      # pylint: disable=no-member
        return self

    def send_keys(self, text):
        if not isinstance(text, list):
            text = keys_to_typing(text)
        for letter in text:
            self.key_down(letter)
            self.key_up(letter)
        return self

class PointerActionsMixin(Interaction):
    """ This class is not supposed to be used on its own, but as a Mixin with KeyInput class """

    def __init__(self):
        super().__init__(self)

    def pointer_down(self, button=MouseButton.LEFT):
        self._add_pointer_down(button)      # pylint: disable=no-member
        return self

    def pointer_up(self, button=MouseButton.LEFT):
        self._add_pointer_up(button)      # pylint: disable=no-member
        return self

    #TODO - needs testing
    def move_to(self, element, x=None, y=None):
        if not isinstance(element, (WebElement, EventFiringWebElement)):
            raise AttributeError("move_to requires a WebElement")
        #this requires some pre-action before the actual action is performed
        action = Action()
        action.add_pre_action(self._get_element_coordinates, args=(element, x, y))
        #don't add to actions yet
        action.add_action_fn(self._add_pointer_move, args=(element, self.DEFAULT_MOVE_DURATION, False))
        self.add_action(action)
        return self
    
    async def _get_element_coordinates(self, element, x=None, y=None):
        if (x is not None) or (y is not None):
            element_rect = await element.rect
            left_offset = element_rect['width'] / 2
            top_offset = element_rect['height'] / 2
            left = -left_offset + (x or 0)
            top = -top_offset + (y or 0)
        else:
            left, top = 0, 0
        return (int(left), int(top))

    def move_by(self, x, y):
        self._add_pointer_move(origin=InteractionType.POINTER, x=int(x), y=int(y))
        return self

    def move_to_location(self, x, y):
        self._add_pointer_move(origin='viewport', x=int(x), y=int(y))
        return self

    def click(self, element=None):
        if element:
            self.move_to(element)
        self.pointer_down(MouseButton.LEFT)
        self.pointer_up(MouseButton.LEFT)
        return self

    def context_click(self, element=None):
        if element:
            self.move_to(element)
        self.pointer_down(MouseButton.RIGHT)
        self.pointer_up(MouseButton.RIGHT)
        return self

    def click_and_hold(self, element=None):
        if element:
            self.move_to(element)
        self.pointer_down()
        return self

    def release(self):
        self.pointer_up()
        return self

    def double_click(self, element=None):
        if element:
            self.move_to(element)
        self.pointer_down(MouseButton.LEFT)
        self.pointer_up(MouseButton.LEFT)
        self.pointer_down(MouseButton.LEFT)
        self.pointer_up(MouseButton.LEFT)
        return self

    def pause(self, duration=0):
        self._add_pause(duration)
        return self
