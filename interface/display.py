"""Write to the display and create textboxes."""

# NOTE: No defaults should be allowed in this module.
# Defaults are handled higher-up

from threading import Lock
from collections import deque
from typing import Iterable, List, Tuple, Deque

import pygame


# Globals
running = True

# Constants
TICK = .01
TEXTBOX_LOCK = Lock()
TEXTBOXES = []

DEFAULT_BORDER_WIDTH = 1
DEFAULT_BORDER_COLOR = (255, 255, 255)
DEFAULT_TEXT_COLOR = (255, 255, 255)

# These must be ordered and do not require fast containment checks
SPLIT_AFTER_CHARS = [' -.,)>]}']
SPLIT_BEFORE_CHARS = ['(<[{']

DIRTY = False

font_objects = {}
FONT_LOCK = Lock()


def _mark_dirty():
    """Mark the display dirty (i.e. set to redraw)."""
    global DIRTY

    DIRTY = True


def render(display: pygame.Surface, fill_color: Iterable[int] = None):
    """Render every textbox if DIRTY."""
    global DIRTY

    if DIRTY:
        if not isinstance(fill_color, type(None)):
            display.fill(fill_color)
        with TEXTBOX_LOCK:
            for textbox in TEXTBOXES:
                textbox.render(display)
        DIRTY = False


def _rewrap():
    """Rewrap all textboxes."""
    for textbox in TEXTBOXES:
        textbox.text_wrap.mark_wrap()


def _resize_display(size: Iterable[int]) -> pygame.Surface:
    """Resize the display to the given size."""
    _mark_dirty()
    _rewrap()
    return pygame.display.set_mode(size, pygame.VIDEORESIZE)


def check_events(display: pygame.Surface,
                 events: Iterable[pygame.event.Event]) -> pygame.Surface:
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
    """Store text supporting fonts and colors."""

    def __init__(self, text: str, font: Font, color: Iterable[int] = None,
                 highlight: Iterable[int] = None):
        self.text = text
        self.font = font
        self.color = color
        if isinstance(color, type(None)):
            self.color = DEFAULT_TEXT_COLOR
        self.highlight = highlight

        self.original_font_repr = repr(self.font)
        self.pos = None

    def set_pos(self, pos: Iterable[int]):
        """Set the Text's pos."""
        if pos != self.pos:
            self.pos = pos

    def reset_font(self):
        """Reset the text's font to the original based.

        Examples
        --------
        >>> _ = pygame.init()
        >>> a = Text("test", Font("courier new", 17))
        >>> a.font
        Font(font_name='courier new', size=17, bold=False, italic=False)
        >>> a.edit_font(size=20, italic=True)
        >>> a.font
        Font(font_name='courier new', size=20, bold=False, italic=True)
        >>> a.reset_font()
        >>> a.font
        Font(font_name='courier new', size=17, bold=False, italic=False)

        """
        self.font = font_objects[self.original_font_repr]
        _mark_dirty()

    def change_font(self, font: Font):
        """Change the Font to a new Font object."""
        self.font = font
        _mark_dirty()

    def edit_font(self, font_name: str = None, size: int = None,
                  bold: bool = None, italic: bool = None):
        """Alter the font of the text.

        Examples
        --------
        >>> _ = pygame.init()
        >>> a = Text("test", Font('courier new', 17))
        >>> a.font
        Font(font_name='courier new', size=17, bold=False, italic=False)
        >>> a.edit_font(size=20, italic=True)
        >>> a.font
        Font(font_name='courier new', size=20, bold=False, italic=True)

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
        if new_font_repr not in font_objects:
            new_font = Font(new_font_name, new_size, new_bold, new_italic)
            font_objects[new_font_repr] = new_font
        self.font = font_objects[new_font_repr]
        _mark_dirty()

    def render(self, display: pygame.Surface):
        """Render the text to the given display."""
        font = self.font.get_pygame_font()
        label = font.render(self.text, 1, self.color, self.highlight)
        display.blit(label, self.pos)

    def get_size(self) -> Tuple[int]:
        """Return the dimensions of the text."""
        return self.font.get_pygame_font().size(self.text)


class _Line():
    """Store text in a line."""

    def __init__(self):
        self.text_list = deque()
        self.width = 0
        self.height = 0

    def _add_text(self, new_text: Text, text_size: Tuple[int]):
        """Add text to the line.

        Examples
        --------
        >>> a = Font("courier new", 20)
        >>> b = Text("_", a)
        >>> c = _Line([b, b, b, b])
        >>> (c.width, c.height)
        (48, 24)

        """
        # Record dimensions while still a list
        # EVENTUALLY: If move sizing outside method, remove method
        self.width += text_size[0]
        self.height = max(self.height, text_size[1])
        self.text_list.append(new_text)
    
    def fit_text(self, text_list: List[Text], box_width: int) -> Deque[Text]:
        """Add text which fits and return the rest."""
        while text_list:

            text = text_list.popLeft()
            text_width, text_height = text.get_size()

            if self.width + text_width <= box_width:
                self._add_text(text, (text_width, text_height))

            else:
                pass  # TODO: Finish

    def __iter__(self):
        """Iterate over the line."""
        for text in self.text_list:
            yield text
            


class _TextWrap():
    """Store wrapped text and handle wrapping."""

    def __init__(self):
        self.wrapped_text_list = deque()
        self.new_text_list = deque()
        self.lines = deque()
        self.unloaded_lines_old = deque()
        self.unloaded_lines_new = deque()

    def _next_line(self):
        """Get the next line to be filled."""
        if self.lines:
            line = self.lines.pop()
        else:
            line = _Line()
        return line

    def _wrap_new_lines(self, coords: List[int]):
        """Wrap text into lines."""
        assert(not isinstance(coords, type(None)))

        x = coords[0]
        text_y_pos = coords[1]
        box_width = coords[2]

        line = self._next_line()

        line_width = line.width

        while self.new_text_list:
            text = self.new_text_list.popleft()
            text_width, _ = text.get_size()

            # Over width
            if line_width + text_width > box_width:
                self.lines.append(line)
                line = _Line()
                text_y_pos += self.lines[-1].height
                line_width = 0
                self.new_text_list.appendleft(text)

                # TODO: Convert to _Line methods to flatten code
                # TODO: Check if will fit on new line
                #       If not, split word
                #       If down to single char, just skip if does not fit

            # Room in line
            else:

                # Add to line
                text.set_pos((line_width + x, text_y_pos))
                line._add_text(text, text.get_size())
                self.wrapped_text_list.append(text)
                line_width += text_width

        if line:
            self.lines.append(line)

        _mark_dirty()

    def mark_wrap(self):
        """Set to be re-wrapped."""
        self.lines.clear()
        # Move old lines back into
        self.wrapped_text_list.reverse()
        self.new_text_list.extendleft(self.wrapped_text_list)
        self.wrapped_text_list.clear()

    def add_text(self, text_list: Iterable[Text]):
        """Add text to the current input."""
        self.new_text_list.extend(text_list)

    def render(self, display: pygame.Surface, coords: List[int]):
        """Render the lines of text."""
        if not self.lines:
            # No lines have been wrapped
            if self.wrapped_text_list:
                # Lines available to wrap
                self._wrap_new_lines(coords)
        if self.new_text_list:
            # New lines need wrapped
            self._wrap_new_lines(coords)

        for line in self.lines:
            for text in line:
                text.render(display)


class TextBox:
    """Display text and supports word-wrap.

    Parameters
    ----------
    pins
        Percentages which correspond to the corners of the box relative to
        the display's resolution

    """

    def __init__(self, pins: Iterable[int]):
        self.pins = pins  # TODO: Support fixed-width/height
        self.border_width = DEFAULT_BORDER_WIDTH
        self.border_color = DEFAULT_BORDER_COLOR

        self.text_wrap = _TextWrap()

        self.coords = None

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

        self.coords = [int(x) for x in coords]

        return self.coords

    def _draw_box(self, display: pygame.Surface):
        """Draw the outline of the textbox to the display."""
        width = display.get_width()
        height = display.get_height()
        coords = self._get_rect(width, height)
        pygame.draw.rect(display, self.border_color, coords, self.border_width)

    def render(self, display: pygame.Surface):
        """Draw the textbox to the given display."""
        self._draw_box(display)
        self.text_wrap.render(display, self.coords)


class InputBox(TextBox):
    """Allow text input and display said text."""

    def __init__(self, display: pygame.Surface):
        super().__init__(display)
        # TODO: Allow use of cursor.


if __name__ == "__main__":
    import doctest
    doctest.testmod()
