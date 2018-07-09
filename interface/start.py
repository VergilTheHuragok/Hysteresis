"""Handle all input and output."""

from threading import Thread
from time import sleep

from .display import render, check_events
import interface.display

import pygame

# Constants
RESOLUTION = (500, 500)

# TODO: cleanup imports


def _interface_loop():
    """Handle all pygame functionality continuously."""
    global display

    pygame.init()

    display = pygame.display.set_mode(RESOLUTION, pygame.RESIZABLE)

    while interface.display.running:
        render(display)
        display = check_events(display)
        pygame.display.flip()  # TODO: only render on change
        sleep(.01)


def init():
    """Create the display and handle all related functionality."""
    interface_thread = Thread(target=_interface_loop)
    interface_thread.setDaemon(True)
    interface_thread.start()
