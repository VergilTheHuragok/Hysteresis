"""Write to the display and create textboxes."""

# NOTE: No defaults should be allowed in this module.
# Defaults are handled higher-up

from threading import Lock
from typing import List, Tuple

import pygame


# Globals
running = True

# Constants
TICK = .01
TEXTBOX_LOCK = Lock()
TEXTBOXES = []

DEFAULT_BORDER_WIDTH = 1
DEFAULT_BORDER_COLOR = (255, 255, 255)

DIRTY = False

font_objects = {}
FONT_LOCK = Lock()


def _mark_dirty():
    """Mark the display dirty (i.e. set to redraw)."""
    global DIRTY

    DIRTY = True


def render(display: pygame.Surface, fill_color: Tuple[int, int, int] = None):
    """Render every textbox if DIRTY."""
    global DIRTY

    if DIRTY:
        if not isinstance(fill_color, type(None)):
            display.fill(fill_color)
        with TEXTBOX_LOCK:
            for textbox in TEXTBOXES:
                textbox.render(display)
        DIRTY = False


def _resize_display(size: List[int]) -> pygame.Surface:
    """Resize the display to the given size."""
    _mark_dirty()
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


def get_font_repr(font_name: str, size: int, bold: bool, italic: bool):
    """Return a string representation of the font object."""
    return (f'Font(font_name=\'{font_name}\', size={size}, bold={bold}, '
            f'italic={italic})')


class Font():
    """Store all values relating to the display of Text."""

    def __init__(self, font_name: str, size: int, bold: bool = False,
                 italic: bool = False):

        self.font_name = font_name
        self.size = size
        self.bold = bold
        self.italic = italic

        self.pygame_font = None
        self._create_pygame_font()

        with FONT_LOCK:
            font_objects[repr(self)] = self

    def _create_pygame_font(self):
        """Create the pygame Font for blitting to Surfaces."""
        self.pygame_font = pygame.font.SysFont(
            self.font_name, self.size, self.bold, self.italic)

    def get_pygame_font(self) -> pygame.font.Font:
        """Return a memoized pygame font created from the font."""
        if isinstance(self.pygame_font, type(None)):
            self._create_pygame_font()
        return self.pygame_font

    def __repr__(self) -> str:
        """Return a string representation of the font object."""
        return get_font_repr(self.font_name, self.size, self.bold, self.italic)

    def __eq__(self, other) -> bool:
        """Compare the font object to another."""
        try:
            font_name = self.font_name == other.font_name
            size = self.size == other.size
            bold = self.bold == other.bold
            italic = self.italic == other.italic
            return font_name and size and bold and italic
        except AttributeError:
            return False


class Text():
    """Store text supporting fonts and colors. """

    def __init__(self, text: str, font: Font):
        self.text = text
        self.font = font
        self.original_font_repr = repr(self.font)

    def reset_font(self):
        """Reset the text's font to the original based."""
        self.font = font_objects[self.original_font_repr]
        _mark_dirty()

    def change_font(self, font_name: str = None, size: int = None,
                    bold: bool = None, italic: bool = None):
        """Alter the font of the text.
        
        Examples
        --------
        >>> import pygame
        >>> pygame.init() # doctest: +ELLIPSIS
        (...
        >>> a = Text("test", Font("monospace", 17))
        >>> a.font
        Font(font_name='monospace', size=17, bold=False, italic=False)
        >>> a.change_font(size=20, italic=True)
        >>> a.font
        Font(font_name='monospace', size=20, bold=False, italic=True)
        """
        global font_objects
        # Get either old or changed values
        new_font_name = self.font.font_name if isinstance(
            font_name, type(None)) else font_name
        new_size = self.font.size if isinstance(size, type(None)) else size
        new_bold = self.font.bold if isinstance(bold, type(None)) else bold
        new_italic = self.font.italic if isinstance(
            italic, type(None)) else italic

        # Check if font already exists
        new_font_repr = get_font_repr(
            new_font_name, new_size, new_bold, new_italic)
        with FONT_LOCK:
            if new_font_repr not in font_objects:
                new_font = Font(new_font_name, new_size, new_bold, new_italic)
                font_objects[new_font_repr] = new_font
            self.font = font_objects[new_font_repr]
        _mark_dirty()

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
