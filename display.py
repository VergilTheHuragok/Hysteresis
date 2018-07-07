"""Write to the display and create textboxes."""

from typing import List

import pygame


def init():
    pygame.init()


class TextBox:
    """Display text and supports word-wrap."""

    def __init__(self, pins):
        self.pins = pins
        self.border_width = 1
        self.border_color = (0, 0, 0)

    def set_pins(self, pins: List[int]):
        """Set the boxes pins"""
        self.pins = pins

    def render(display):
