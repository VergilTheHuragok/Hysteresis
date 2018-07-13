"""Write to the display and create textboxes."""

# NOTE: No defaults should be allowed in this module.
# Defaults are handled higher-up

from threading import Lock
from collections import deque
from typing import Iterable, List, Tuple, Deque

import pygame


# CLEAN: Determine necessary locations for _mark_dirty()

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
SPLIT_CHARS_AFTER = [' -.,)>]}']
SPLIT_CHARS_BEFORE = ['(<[{']
SPLIT_CHARS_ALL = SPLIT_CHARS_AFTER + SPLIT_CHARS_BEFORE
SPLIT_CHARS_SET = set(SPLIT_CHARS_ALL)

DIRTY = False

font_objects = {}
FONT_LOCK = Lock()


def _split_chars_sort(char: Iterable[str]) -> int:
    """Sort an Iterable of split chars."""
    return SPLIT_CHARS_ALL.index(char)


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

        self.split_sections = []  # Need fast indexing

    def set_pos(self, pos: Iterable[int]):
        """Set the Text's pos."""
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

    def set_font(self, font: Font):
        """Set the Font to a new Font object."""
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

    def split(self) -> int:
        """Split at the optimal location.

        Returns
        -------
        The index of the created splint_ind in self.split_sections.

        """
        possible_split_points = {}
        for ind, char in enumerate(self.text):
            if char in SPLIT_CHARS_SET:
                # Only take split char closest to end
                possible_split_points[char] = ind

        if not possible_split_points:
            return None

        split_chars_sorted = sorted(possible_split_points.keys(),
                                    key=_split_chars_sort)
        split_char = split_chars_sorted[0]
        split_ind = possible_split_points[split_char]
        self.split_sections.append(split_ind)
        return len(self.split_sections) - 1

    def _get_text_section(self, split_section: int = None):
        """Get the text which should be rendered for this section."""
        if self.split_sections:
            assert(not isinstance(split_section, type(None)))

            start = None
            end = None
            if split_section == 0:
                # TODO: Exclusive?
                end = self.split_sections[0]
            elif split_section == len(self.split_sections) - 1:
                start = self.split_sections[-1]
            else:
                start = self.split_sections[split_section]
                end = self.split_sections[split_section + 1]

            text_slice = slice(start, end)
            text = self.text[text_slice]
        else:
            text = self.text

        return text

    def render(self, display: pygame.Surface, split_section: int = None):
        """Render the text to the given display.

        Parameters
        ----------
        split_section
            If text contains a split, a section number must be provided.

        """
        text = self._get_text_section(split_section)
        font = self.font.get_pygame_font()
        label = font.render(text, 1, self.color, self.highlight)
        display.blit(label, self.pos)

    def get_size(self, split_section: int = None) -> Tuple[int]:
        """Return the dimensions of the text."""
        text = self._get_text_section(split_section)
        return self.font.get_pygame_font().size(text)


class _Line():
    """Store text in a line."""

    def __init__(self):
        self.text_list = deque()
        self.width = 0
        self.height = 0
        self.pos = None

        self.split_sections = []

    def set_pos(self, pos: Tuple[int]):
        """Set the pos of the _Line."""
        self.pos = pos

    def fit_text(self, box_text_list: Deque[Text], box_width: int,
                 split_sections: Deque[int]) -> Deque[Text]:
        """Add text which fits and return the rest.

        Returns
        -------
        Text added to the line.

        Examples
        --------
        >>> a = _Line()
        >>> b = Font("monospace", 20)
        >>> c = Text("-", b)
        >>> a.fit_text(deque([c, c, c, c]), 200)
        >>> (a.width, a.height)
        (48, 24)

        """
        text_x = 0
        added_text = deque()
        following_split_sections = deque()
        while box_text_list:
            text = box_text_list.popleft()
            if text.split_sections:
                split_section = split_sections.pop()
                split_sections.append(split_section)
            else:
                split_section = None

            text_width, text_height = text.get_size(split_section)

            if self.width + text_width <= box_width:
                self.width += text_width
                self.height = max(self.height, text_height)
                text_x += text_width
                self.text_list.append(text)
                added_text.append(text)

            elif text_width > box_width:
                split_section = text.split()
                if not isinstance(split_section, type(None)):
                    self.split_sections.append(split_section)
                    following_split_sections.append(split_section + 1)

                    text_width, text_height = text.get_size(split_section)

                    self.width += text_width
                    self.height = max(self.height, text_height)
                    text_x += text_width
                    self.text_list.append(text)
                    added_text.append(text)
                    box_text_list.appendleft(text)

                added_text.append(text)
            else:
                box_text_list.appendleft(text)
                break
            
            if text.split_sections:
                # If this text contains a split section, add section to line
                assert(split_sections)
                self.split_sections.append(split_sections.popleft())

        return added_text, following_split_sections

    def render(self, display: pygame.Surface):
        """Render the line to the display."""
        text_x = 0
        for text in self.text_list:
            text.set_pos((self.pos[0] + text_x, self.pos[1]))
            text.render(display)
            text_x += text.get_size()[0]

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

        self.pos = None

        self.new_line_y = 0

    def _next_line(self):
        """Get the next line to be filled."""
        if self.lines:
            line = self.lines.pop()
        else:
            line = _Line()
        return line

    def _wrap_new_lines(self):
        """Wrap text into lines."""
        assert(not isinstance(self.pos, type(None)))

        box_width = self.pos[2]
        line = self._next_line()
        split_sections = deque()
        while self.new_text_list:

            added_text, new_split_sections = line.fit_text(
                self.new_text_list, box_width, split_sections)
            split_sections.extend(new_split_sections)

            self.wrapped_text_list.extend(added_text)
            self.lines.append(line)
            line = _Line()

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

    def render(self, display: pygame.Surface, pos: List[int]):
        """Render the lines of text."""
        self.pos = pos

        if not self.lines:
            # No lines have been wrapped
            if self.wrapped_text_list:
                # Lines available to wrap
                self._wrap_new_lines()
        if self.new_text_list:
            # New lines need wrapped
            self._wrap_new_lines()

        line_y = self.pos[1]
        for line in self.lines:
            line.set_pos((self.pos[0], line_y))
            line.render(display)
            line_y += line.height


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

        self.pos = None

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
        pos = [
            self.pins[0] * width,
            self.pins[1] * height
        ]
        pos.append(self.pins[2] * width - pos[0])
        pos.append(self.pins[3] * height - pos[1])

        self.pos = [int(x) for x in pos]

        return self.pos

    def _draw_box(self, display: pygame.Surface):
        """Draw the outline of the textbox to the display."""
        width = display.get_width()
        height = display.get_height()
        pos = self._get_rect(width, height)
        pygame.draw.rect(display, self.border_color, pos, self.border_width)

    def render(self, display: pygame.Surface):
        """Draw the textbox to the given display."""
        self._draw_box(display)
        self.text_wrap.render(display, self.pos)


class InputBox(TextBox):
    """Allow text input and display said text."""

    def __init__(self, display: pygame.Surface):
        super().__init__(display)
        # TODO: Allow use of cursor.


if __name__ == "__main__":
    import doctest
    doctest.testmod()
