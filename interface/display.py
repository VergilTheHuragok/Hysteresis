"""Write to the display and create textboxes."""

from threading import Lock
from typing import List

import pygame


# Globals
running = True

# Constants
TICK = .01
TEXTBOX_LOCK = Lock()
TEXTBOXES = []

DEFAULT_BORDER_WIDTH = 1
DEFAULT_BORDER_COLOR = (255, 255, 255)


def render(display: pygame.Surface):
    """Render every textbox."""
    with TEXTBOX_LOCK:
        for textbox in TEXTBOXES:
            textbox.render(display)


def _resize_display(size: List[int]) -> pygame.Surface:
    """Resize the display to the given size."""
    return pygame.display.set_mode(size, pygame.VIDEORESIZE)


def check_events(display: pygame.Surface, events: List[pygame.event.Event]) \
        -> pygame.Surface:
    """Check pygame display events and execute accordingly."""
    global running

    for event in events:
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            display = _resize_display(event.dict['size'])

    return display


class Text():
    """Store text supporting fonts and colors."""

    def __init__(self, text: str):
        self.text = text

    def render(self, display: pygame.Surface):
        """Render the text to the given display."""
        # TODO: Render text
        pass


class _Line():
    """Store a line of text supporting fonts and colors."""

    def __init__(self):

        self.text_list = []

    def render(self, display: pygame.Surface):
        """Render all text in the line to the given display."""
        for text in self.text_list:
            text.render(display)


class _TextList():
    """Store lines of text supporting fonts and colors."""

    def __init__(self):

        self.master_text_list = []
        self.lines = []

    def __iadd__(self, text_list: List[Text]):
        """Add a list of Text to this text_list."""
        self.master_text_list += text_list

    def _wrap(self):
        """Wrap Text into _Lines."""
        # TODO: Wraps
        pass

    def render(self, display: pygame.Surface):
        """Render each line to the display."""
        # TODO: Check if needs wrapped at render-time
        for line in self.lines:
            line.render(display)


class TextBox:
    """Display text and supports word-wrap.

    Parameters
    ----------
    pins
        Percentages which correspond to the corners of the box relative to
        the display's resolution

    """

    def __init__(self, pins: List[int]):
        self.pins = pins  # TODO: Support fixed-width/height
        self.border_width = DEFAULT_BORDER_WIDTH
        self.border_color = DEFAULT_BORDER_COLOR

        self.text_list = _TextList()

        with TEXTBOX_LOCK:
            TEXTBOXES.append(self)

    def _get_rect(self, width: int, height: int) -> List[int]:
        """Get coordinates based on self.pins and display resolution.

        Parameters
        ----------
        width
            The width of the display
        height
            The height of the display

        Examples
        --------
        >>> a = TextBox([0, 0, .5, 1])
        >>> a._get_rect(500, 300)
        [0, 0, 250, 300]

        >>> a = TextBox([.3, .3, .6, 1])
        >>> a._get_rect(100, 250)
        [30, 75, 30, 175]

        """
        # Use pins as percentages to determine corresponding coordinate
        coords = [
            self.pins[0] * width,
            self.pins[1] * height
        ]
        coords.append(self.pins[2] * width - coords[0])
        coords.append(self.pins[3] * height - coords[1])

        coords = [int(x) for x in coords]

        return coords

    def _draw_box(self, display: pygame.Surface):
        """Draw the outline of the textbox to the display."""
        width = display.get_width()
        height = display.get_height()
        coords = self._get_rect(width, height)
        pygame.draw.rect(display, self.border_color, coords, self.border_width)

    def add_text(self, text_list: List[Text]):
        """Add text to the current input."""
        self.text_list += text_list

    def render(self, display: pygame.Surface):
        """Draw the textbox to the given display."""
        self._draw_box(display)
        self.text_list.render(display)


class InputBox(TextBox):
    """Allow text input and display said text."""

    def __init__(self, display: pygame.Surface):
        super().__init__(display)
        # TODO: Allow use of cursor.


if __name__ == "__main__":
    import doctest
    doctest.testmod()
