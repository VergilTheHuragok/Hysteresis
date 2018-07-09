"""Handle all pygame input."""

from typing import List

import pygame


def check_events(events: List[pygame.event.Event]):
    """Handle all pygame input events."""
    for event in events:
        if event.type == pygame.KEYDOWN:
            pass  # TODO: pass chars to focused inputbox