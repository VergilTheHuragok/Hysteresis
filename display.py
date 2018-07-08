"""Write to the display and create textboxes."""
from threading import Lock, Thread
from time import sleep
from typing import List

import pygame


# Globals
running = True
display = None

# Constants
RESOLUTION = (500, 500)
TICK = .01
TEXTBOX_LOCK = Lock()
TEXTBOXES = []

DEFAULT_BORDER_WIDTH = 1
DEFAULT_BORDER_COLOR = (255, 255, 255)


def _render():
    """Render every textbox."""
    with TEXTBOX_LOCK:
        for textbox in TEXTBOXES:
            textbox.render()
    pygame.display.flip()


def _render_loop():
    """Render every textbox continuously."""
    pygame.init()  # IMPORTANT: Use tkinter instead. Work with multithreading?

    while running:
        _render()
        sleep(TICK)


def _resize_display(size: List[int]):
    """Resize the display to the given size."""
    global display

    display = pygame.display.set_mode(size, pygame.VIDEORESIZE)


def _event_loop():
    """Check pygame events and execute accordingly."""
    global running

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            _resize_display(event.dict['size'])


def init():
    """Initialize pygame and local vars."""
    global display

    display = pygame.display.set_mode(RESOLUTION, pygame.RESIZABLE)

    render_loop = Thread(target=_render_loop)
    render_loop.setDaemon(True)
    render_loop.start()

    event_loop = Thread(target=_event_loop)
    event_loop.setDaemon(True)
    event_loop.start()


class TextBox:
    """Display text and supports word-wrap.

    Parameters
    ----------
    pins
        Percentages which correspond to the corners of the box relative to
        the display's resolution

    """

    def __init__(self, pins: List[int]):
        self.pins = pins
        self.border_width = DEFAULT_BORDER_WIDTH
        self.border_color = DEFAULT_BORDER_COLOR
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

        """
        # Use pins as percentages to determine corresponding coordinate
        coords = [*range(0, 4)]
        for i, pin in enumerate(self.pins):

            if i % 2 == 0:
                # Pin is even
                max_length = width
            else:
                max_length = height

            coords[i] = int(pin * max_length)

        return coords

    def _draw_box(self):
        """Draw the outline of the textbox to the display."""
        width = display.get_width()
        height = display.get_height()
        coords = self._get_rect(width, height)
        pygame.draw.rect(display, self.border_color, coords, self.border_width)

    def render(self):
        """Draw the textbox to the given display."""
        self._draw_box()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
