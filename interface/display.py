"""Write to the display and create textboxes."""

from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Deque, Iterable, List, Optional, Set, Tuple
from itertools import islice
import time

import pygame

# TODO: Move constants to a global context as with the decimal class

# Globals
RUNNING = True

# Constants
TICK = 0.01
TEXTBOX_LOCK = Lock()
textboxes = []
active_box = None

DEFAULT_BORDER_WIDTH = 1
DEFAULT_BORDER_COLOR = (255, 255, 255)
DEFAULT_INDICATOR_COLOR = (125, 125, 255)
DEFAULT_TEXT_COLOR = (255, 255, 255)
DEFAULT_CURSOR_COLOR = (255, 0, 0)
DEFAULT_CURSOR_WIDTH = 1

# TextWrap Constants
# N = new text object
SPLIT_CHARS_AFTER = list(" -.,!?;/\\)>]}+*&^%`")
SPLIT_CHARS_AFTER_SET = set(SPLIT_CHARS_AFTER)

SPLIT_CHARS_BEFORE = list("(<[{_$#@|~N")
# N splits at end of text object

SPLIT_CHARS_ALL = SPLIT_CHARS_AFTER + SPLIT_CHARS_BEFORE
SPLIT_CHARS_ALL_SET = set(SPLIT_CHARS_ALL)

DIRTY = False

font_objects = {}
FONT_LOCK = Lock()

SCROLL_AMOUNT = 1
DRAG_DECELERATION = 35
DRAG_FACTOR = 1
DRAG_DEADZONE = 20

CURSOR_KEYS = {
    pygame.K_LEFT: -1,
    pygame.K_RIGHT: 1,
    pygame.K_DOWN: "d",
    pygame.K_UP: "u",
}
CURSOR_REPEAT_TIME = 0.00005
CURSOR_REPEAT_THRESHOLD = 0.5


def _mark_dirty():
    """Mark the display dirty (i.e. set to redraw)."""
    global DIRTY

    DIRTY = True


def _coast_scrolls():
    """Find textboxes which have coasting scrolls and perform scroll."""

    for box in textboxes:
        box.text_wrap.coast_scroll()


def _check_held_keys():
    """Check for keys being held."""

    if isinstance(active_box, type(None)):
        # No active box
        return
    if not isinstance(active_box, InputBox):
        # Active box is not an input box
        return
    if isinstance(active_box.cursor_key_press_time, type(None)):
        # Key press not yet handled by active_box
        return

    keys = pygame.key.get_pressed()
    if 1 not in keys:
        return

    pressed_keys = [ind for ind, key in enumerate(keys) if key == 1]
    for key in pressed_keys:
        if key in CURSOR_KEYS:
            active_box.handle_cursor_key(key)


def render(display: pygame.Surface, fill_color: Iterable[int] = None):
    """Render every textbox if DIRTY."""
    global DIRTY

    _coast_scrolls()
    _check_held_keys()

    if DIRTY:
        if not isinstance(fill_color, type(None)):
            display.fill(fill_color)
        with TEXTBOX_LOCK:
            for textbox in textboxes:
                textbox.render(display)
        DIRTY = False


def get_time():
    """Return the current time in millis."""
    return time.time()


def _rewrap():
    """Rewrap all textboxes."""
    for textbox in textboxes:
        with textbox.text_wrap.text_lock:
            textbox.text_wrap.mark_wrap()


def _resize_display(size: Iterable[int]) -> pygame.Surface:
    """Resize the display to the given size."""
    _mark_dirty()
    _rewrap()
    return pygame.display.set_mode(size, pygame.VIDEORESIZE)


def get_dims(display: pygame.Surface) -> Tuple[int]:
    """Get the dimensions of the screen."""

    return display.get_width(), display.get_height()


def activate_box(box):
    """Set a textbox to active."""
    global active_box
    active_box = box


def check_events(
    display: pygame.Surface, events: Iterable[pygame.event.Event]
) -> pygame.Surface:
    """Check pygame display events and execute accordingly."""
    global RUNNING

    for event in events:
        if event.type == pygame.QUIT:
            RUNNING = False
        elif event.type == pygame.VIDEORESIZE:
            display = _resize_display(event.dict["size"])
        elif event.type == pygame.KEYUP:
            for box in textboxes:
                if isinstance(box, InputBox):
                    box.reset_cursor_repeat()

        if "pos" in event.dict:
            for box in textboxes:
                if box.handle_event(event, display):
                    break
        elif not isinstance(active_box, type(None)):
            active_box.handle_event(event, display)
    return display


def get_font_repr(font_name: str, size: int, bold: bool, italic: bool):
    """Return a string representation of the font object."""
    return f"Font(font_name='{font_name}', size={size}, bold={bold}, italic={italic})"


class Font:
    """Store all values relating to the display of Text."""

    def __init__(
        self, font_name: str, size: int, bold: bool = False, italic: bool = False
    ):

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
            self.font_name, self.size, self.bold, self.italic
        )

    def get_pygame_font(self) -> pygame.font.Font:
        """Return a memoized pygame font created from the font."""
        if isinstance(self.pygame_font, type(None)):
            self._create_pygame_font()
        return self.pygame_font

    def edit(
        self,
        font_name: str = None,
        size: int = None,
        bold: bool = None,
        italic: bool = None,
    ) -> Font:  # NOQA: F821
        """Create a new font based off this one.

        Examples
        --------
        >>> _ = pygame.init()
        >>> a = Font('courier new', 17)
        >>> a
        Font(font_name='courier new', size=17, bold=False, italic=False)
        >>> b = a.edit(size=20, italic=True)
        >>> a
        Font(font_name='courier new', size=17, bold=False, italic=False)
        >>> b
        Font(font_name='courier new', size=20, bold=False, italic=True)

        """
        global font_objects
        # Get either old or changed values
        new_font_name = (
            self.font_name if isinstance(font_name, type(None)) else font_name
        )
        new_size = self.size if isinstance(size, type(None)) else size
        new_bold = self.bold if isinstance(bold, type(None)) else bold
        new_italic = self.italic if isinstance(italic, type(None)) else italic

        # Check if font already exists
        new_font_repr = get_font_repr(new_font_name, new_size, new_bold, new_italic)
        if new_font_repr not in font_objects:
            new_font = Font(new_font_name, new_size, new_bold, new_italic)
            with FONT_LOCK:
                font_objects[new_font_repr] = new_font
        return font_objects[new_font_repr]

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


class Text:
    """Store text supporting fonts and colors."""

    def __init__(
        self,
        text: str,
        font: Font,
        color: Iterable[int] = None,
        highlight: Iterable[int] = None,
        new_line: bool = False,
        label: str = None,
    ):
        self.text_segment = text
        self.all_text = text

        self.font = font
        self.color = color
        if isinstance(color, type(None)):
            self.color = DEFAULT_TEXT_COLOR
        self.highlight = highlight

        self.new_line = new_line
        self.label = label

        self.original_font_repr = repr(self.font)
        self.pos = None

    def set_pos(self, pos: Iterable[int]):
        """Set the Text's pos."""
        self.pos = pos

    def change_text(self, text):
        """Change the original text.
        
        Line likely will need rewrapped.
        """
        self.all_text = text
        self.text_segment = text

    def reset_text(self):
        """Reset the text's text_segment to the original, full string."""
        self.text_segment = self.all_text

    def set_text_segment(self, text_segment: Optional[str]):
        """Set the text_segment until .reset_text() is called."""
        if not isinstance(text_segment, type(None)):
            self.text_segment = text_segment

    def reset_font(self):
        """Reset the text's font to the original based.

        Examples
        --------
        >>> _ = pygame.init()
        >>> a = Text("test", Font("courier new", 17))
        >>> a.font
        Font(font_name='courier new', size=17, bold=False, italic=False)
        >>> a.set_font(a.font.edit(size=20, italic=True))
        >>> a.font
        Font(font_name='courier new', size=20, bold=False, italic=True)
        >>> a.reset_font()
        >>> a.font
        Font(font_name='courier new', size=17, bold=False, italic=False)

        """
        self.set_font(font_objects[self.original_font_repr])
        _mark_dirty()

    def set_font(self, font: Font):
        """Set the Font to a new Font object."""
        width = self.get_size()[0]
        self.font = font
        new_width = self.get_size(self.text_segment)[0]
        if width != new_width:
            _rewrap()
        _mark_dirty()

    def _force_split(self, remaining_width: int, box_width: int) -> Tuple[str]:
        """Split at the location closest to the box border.

        Parameters
        ----------
        remaining_width
            The amount of space remaining in which to fit a section of text.
        box_width
            The max width for a line.

        Returns
        -------
        Tuple[0]
            A section of text which fits in the remaining width.
        Tuple[1]
            The remaining text which must be added to a new line.

        """
        best_ind = None
        for ind in range(0, len(self.text_segment)):
            segment = self.text_segment[: ind + 1] + "-"
            segment_width = self.get_size(segment)[0]
            if ind > 0:
                best_ind = ind - 1
            if segment_width > remaining_width:
                if ind == 0 and remaining_width == box_width:
                    # Single char does not fit on a line to itself
                    self.text_segment = ""
                break

        if isinstance(best_ind, type(None)):
            # Nothing fits on this line, put all on next
            best_segment = ""
            other_segment = self.text_segment
        else:
            best_segment = self.text_segment[: best_ind + 1] + "-"
            other_segment = self.text_segment[best_ind + 1 :]
        self.text_segment = best_segment
        return (best_segment, other_segment)

    def split(self, remaining_width: int, box_width: int) -> Tuple[str]:
        """Split at the optimal location.

        Parameters
        ----------
        remaining_width
            The amount of space remaining in which to fit a section of text.
        box_width
            The max width for a line.

        Returns
        -------
        Tuple[0]
            A section of text which fits in the remaining width.
        Tuple[1]
            The remaining text which must be added to a new line.

        Examples
        --------
        >>> a = Font('Courier New', 20)
        >>> b = Text('aaa-bbbbb', a)
        >>> b.split(50, 50)
        ('aaa-', 'bbbbb')

        >>> a = Font('Courier New', 20)
        >>> b = Text('aaa(bbbbb)', a)
        >>> b.split(50, 50)
        ('aaa', '(bbbbb)')

        """

        def _split_chars_sort(char: Iterable[str]) -> int:
            """Sort an Iterable of split chars."""
            return SPLIT_CHARS_ALL.index(char)

        possible_split_points = {}
        if remaining_width < box_width and "N" in SPLIT_CHARS_ALL_SET:
            possible_split_points["N"] = ("", self.text_segment)

        for ind, char in enumerate(self.text_segment):
            split_ind = ind
            if char in SPLIT_CHARS_AFTER_SET:
                split_ind += 1
            elif ind == 0 and remaining_width == box_width:
                # Cannot split before first char on a new_line
                continue
            text_segment = self.text_segment[:split_ind]
            other_segment = self.text_segment[split_ind:]
            text_segment_width = self.get_size(text_segment)[0]

            if text_segment_width <= remaining_width:
                if char in SPLIT_CHARS_ALL_SET and char != "N":
                    possible_split_points[char] = (text_segment, other_segment)
            else:
                break  # Already outside remaining width

        if possible_split_points:
            split_chars_sorted = sorted(
                possible_split_points.keys(), key=_split_chars_sort
            )
            best_split_char = split_chars_sorted[0]
            best_segments = possible_split_points[best_split_char]
            self.text_segment = best_segments[0]
            return best_segments
        return self._force_split(remaining_width, box_width)

    def render(self, display: pygame.Surface):
        """Render the text to the given display.

        Parameters
        ----------
        split_section
            If text contains a split, a section number must be provided.

        """
        font = self.font.get_pygame_font()
        label = font.render(self.text_segment, 1, self.color, self.highlight)
        display.blit(label, self.pos)

    def get_size(self, text: str = None) -> Tuple[int]:
        """Return the dimensions of the text.

        Parameters
        ----------
        text
            text to determine the size of. If None, check self.text.

        """
        if isinstance(text, type(None)):
            text = self.text_segment
        return self.font.get_pygame_font().size(text)


class _Line:
    """Store text in a line."""

    def __init__(self):
        self.text_list = deque()
        self.width = 0
        self.height = 0
        self.pos = None

        self.text_segments = {}

        self.new_line = False

    def set_pos(self, pos: Tuple[int]):
        """Set the pos of the _Line."""
        self.pos = pos

    def fit_text(
        self, box_text_list: Deque[Text], box_width: int
    ) -> Tuple[Deque[Text], Tuple[int, str]]:
        """Add text which fits and return the rest.

        Parameters
        ----------
        box_text_list
            The list of text contained by the line's parent box.
            List of text to be wrapped.
        box_width
            The width of the textbox to which the line belongs.

        Returns
        -------
        Tuple[0]
            Text added to the line.
        Tuple[1]
            Remaining segment of text.

        Examples
        --------
        >>> a = _Line()
        >>> b = Font("monospace", 20)
        >>> c = Text("-", b)
        >>> d = a.fit_text(deque([c, c, c, c]), 200)
        >>> (a.width, a.height)
        (12, 24)

        """

        def text_needs_wrapped():
            """Check if text still needs wrapped."""
            return box_text_list

        added_text = deque()
        following_text_segment = ()

        while text_needs_wrapped() and not self.new_line:
            text = box_text_list.popleft()
            text_id = id(text)

            if text in self.text_list:
                # This should only occur if text object reached bottom
                following_text_segment = (text_id, text.text_segment)
                box_text_list.appendleft(text)
                break

            if text_id in self.text_segments:
                text_segment = self.text_segments[text_id]
                text.set_text_segment(text_segment)

            text_width, text_height = text.get_size()

            if self.width + text_width <= box_width:
                self.width += text_width
                self.height = max(self.height, text_height)
                self.text_list.append(text)
                added_text.append(text)
                if text.new_line:
                    self.new_line = True
                    break

            else:
                remaining_width = box_width - self.width

                text_segments = text.split(remaining_width, box_width)
                if text_segments[0]:
                    self.text_segments[text_id] = text_segments[0]

                    text_width, text_height = text.get_size()

                    self.width += text_width
                    self.height = max(self.height, text_height)
                    self.text_list.append(text)
                if text_segments[1]:
                    following_text_segment = (text_id, text_segments[1])
                    box_text_list.appendleft(text)
                added_text.append(text)
                break

        return added_text, following_text_segment

    def get_text_segment(self, text):
        """Get the segment of a text object in this line."""
        text_id = id(text)
        if text_id in self.text_segments:
            text_segment = self.text_segments[text_id]
            return text_segment
        return text.text_segment

    def get_line_string(self):
        """Get the string of text stored by the line."""
        string = ""
        for text in self.text_list:
            string += self.get_text_segment(text)
        return string

    def render(self, display: pygame.Surface):
        """Render the line to the display."""
        text_x = 0
        for text in self.text_list:
            text_segment = self.get_text_segment(text)
            text.set_text_segment(text_segment)
            text.set_pos((self.pos[0] + text_x, self.pos[1]))
            text.render(display)
            text_x += text.get_size()[0]

    def get_rect(self):
        """Get the bounding rect for this line."""
        if isinstance(self.pos, type(None)):
            raise Exception("Line not yet rendered.")
        return [*self.pos, self.width, self.height]

    def within_line(self, x: int, y) -> bool:
        """Check if given coordinates are within the line.

        Parameters
        ----------
        x
            x coordinate of point
        y
            y coordinate of point

        """
        rect = self.get_rect()
        coords = [rect[0], rect[1], rect[2] + rect[0], rect[3] + rect[1]]
        return coords[0] < x < coords[2] and coords[1] < y < coords[3]

    def __iter__(self):
        """Iterate over the line."""
        for text in self.text_list:
            yield text

    def __getitem__(self, ind):
        """Get a Text object at the index."""
        return self.text_list[ind]

    def __contains__(self, text_id):
        """Check if text_id is present in line."""
        for text in self:
            if id(text) == text_id:
                return True
        return False

    def __bool__(self):
        """Get a boolean state of this line.

        True if contains text.
        """
        return bool(self.text_list)


class _TextWrap:
    """Store wrapped text and handle wrapping."""

    # TODO: Store text older than a given num of lines in a file
    #   use repr of text objects to store/retrieve
    #   This should all take place at a higher level
    #       Just take text objects from textbox and store reprs in file
    #       Textbox can then be recreated at this higher level from reprs in file

    def __init__(self):
        self.wrapped_text_list = deque()
        self.new_text_list = deque()

        self.current_height = 0

        self.pos = None

        self.text_lock = Lock()

        self.lines = deque()
        self.line_num = 0
        self.remaining_segments = {}

        self.drag_speed = 0
        self.drag_start_time = None
        self.drag_end_time = None
        self.dragged_lines = 0
        self.drags_to_go = 0
        self.drag_start_pos = None

        self.was_at_bottom = False

    def _next_line(self):
        """Get the next line to be filled."""
        if self.lines:
            line = self.lines.pop()
            self.current_height -= line.height
        else:
            line = _Line()
        return line

    def _wrap_new_lines(self, all_=False):
        """Wrap text into lines."""

        def text_needs_wrapped():
            """Check if text still needs wrapped."""
            return self.new_text_list

        def within_height():
            """Check if the current wrapped lines are shorter than height of box."""
            return self.current_height < self.pos[3]

        lines_added = 0

        if text_needs_wrapped() and (all_ or within_height()):
            assert not isinstance(self.pos, type(None))

            box_width = self.pos[2]
            line = self._next_line()

            new_text_segment = None

            while text_needs_wrapped() or line.text_segments:
                # NOTE: Final line has text_segment but no text remains to be wrapped

                # Add segments lost after ceasing previous wrap at bottom
                for text_id, segment in tuple(self.remaining_segments.items()):
                    if text_id not in line.text_segments and not line.new_line:
                        line.text_segments[text_id] = segment
                        del self.remaining_segments[text_id]

                added_text, new_text_segment = line.fit_text(
                    self.new_text_list, box_width
                )

                # Check if remaining segments added to line were unused
                for text_id, segment in tuple(line.text_segments.items()):
                    if text_id not in line:
                        self.remaining_segments[text_id] = segment
                        del line.text_segments[text_id]

                if not all_ and self.current_height + line.height > self.pos[3]:
                    if new_text_segment or line.text_segments:

                        # Move line and new segments into remaining segments
                        segment = ""
                        text_id = id(line[0])
                        for text_id in map(id, line):
                            if text_id in line.text_segments:
                                segment = line.text_segments[text_id]
                            if new_text_segment and text_id == new_text_segment[0]:
                                segment += new_text_segment[1]
                                new_text_segment = ()
                            if segment:
                                self.remaining_segments[text_id] = segment
                            segment = ""

                        if new_text_segment:
                            text_id = new_text_segment[0]
                            segment = new_text_segment[1]
                            self.remaining_segments[text_id] = segment
                            new_text_segment = ()

                        line.text_segments.clear()
                    line.text_list.reverse()
                    self.new_text_list.extendleft(line.text_list)
                    self._purge_segments([self.new_text_list], False)
                    break

                self.wrapped_text_list.extend(added_text)
                self._purge_segments([self.wrapped_text_list], False)
                self.lines.append(line)
                lines_added += 1
                if len(self.lines) >= self.line_num:
                    self.current_height += line.height

                line = _Line()

                if new_text_segment:
                    if new_text_segment[0] not in self.remaining_segments:
                        # Convert tuple to dict
                        text_id = new_text_segment[0]
                        text_segment = new_text_segment[1]
                        line.text_segments[text_id] = text_segment
        return lines_added

    def _purge_segments(self, lists=None, reset_segment=True):
        """Clear split segments."""

        def _purge_segments_from_list(text_list: Deque, used_text_ids: Set):
            """Clear split segments from the given list in place."""
            checked_text_list = deque()
            while text_list:
                text = text_list.pop()
                text_id = id(text)
                if text_id not in used_text_ids:
                    checked_text_list.appendleft(text)
                    used_text_ids.add(text_id)
                    if reset_segment:
                        text.reset_text()

            text_list.extend(checked_text_list)

        used_text_ids = set()

        if isinstance(lists, type(None)):
            _purge_segments_from_list(self.wrapped_text_list, used_text_ids)
            _purge_segments_from_list(self.new_text_list, used_text_ids)
        else:
            for list_ in lists:
                _purge_segments_from_list(list_, used_text_ids)

    def mark_wrap(self):
        """Set to be re-wrapped."""
        # TODO: Only wrap first line changed and past.
        #       Save line_num between wraps unless after changed line
        #       set to changed line in that case
        self._stop_coast()
        self.lines.clear()
        self.current_height = 0
        # Move old lines back into
        self._purge_segments()
        self.wrapped_text_list.reverse()
        self.new_text_list.extendleft(self.wrapped_text_list)
        self.wrapped_text_list.clear()
        self.line_num = 0
        self.remaining_segments.clear()

    def get_box_string(self):
        """Get all text in box as a string."""
        string = ""
        for line in self.lines:
            for text in line:
                string += line.get_text_segment(text)
        for text in self.new_text_list:
            string += text.all_text
        return string

    def add_text(self, text_list: Iterable[Text]):
        """Add text to the current input."""
        with self.text_lock:
            self.new_text_list.extend(text_list)
        _mark_dirty()

    def get_labeled_text(self, label):
        """Get all text with given label.

        Make sure to rewrap and mark dirty.
        """
        all_text = self.wrapped_text_list + self.new_text_list
        return list(filter(lambda x: x.label == label, all_text))

    def change_text(self, label, string):
        """Change all text objects with the given label to the new text."""
        with self.text_lock:
            for text in self.get_labeled_text(label):
                text.change_text(string)
            self.mark_wrap()
        _mark_dirty()

    def _get_lines(self):
        """Return a deque of the current lines from scroll."""
        return islice(self.lines, self.line_num, None)

    def _get_final_line_num(self):
        """Get the last line num which fits on screen."""
        height = 0
        num = 0
        for num, line in enumerate(self._get_lines()):
            height += line.height
            if height > self.pos[3]:
                return num - 1 + self.line_num
        return num + self.line_num

    def calculate_height(self):
        """Reset the current height."""
        self.current_height = 0
        for line in self._get_lines():
            self.current_height += line.height

    def scroll_lines(self, num_lines):
        """Scroll a given number of lines."""
        self.line_num += num_lines
        self.line_num = max(0, self.line_num)
        to_scroll = len(self.lines) - self.line_num - 1
        if to_scroll < 0:
            # Ensure we don't scroll past the last line
            self.scroll_lines(to_scroll)
        self.calculate_height()
        _mark_dirty()

    def _stop_coast(self):
        """Stop coasting."""
        self.drag_speed = 0
        self.drag_end_time = None
        self.dragged_lines = 0
        self.drags_to_go = 0

    def coast_scroll(self):
        """Continue a scroll based on current drag speed."""
        if self.drag_speed and (
            abs(self.drag_speed) > DRAG_DEADZONE or self.drags_to_go
        ):
            # Only coast if already are or above deadzone
            current_time = get_time()
            time_diff = current_time - self.drag_end_time
            self.drags_to_go += self.drag_speed * time_diff
            self.drag_end_time = current_time
            if self.drag_speed < 0:
                self.drag_speed += DRAG_DECELERATION * time_diff
                self.drag_speed = min(0, self.drag_speed)
            elif self.drag_speed > 0:
                self.drag_speed -= DRAG_DECELERATION * time_diff
                self.drag_speed = max(0, self.drag_speed)
            if abs(self.drags_to_go) > 1:
                drag = int(self.drags_to_go)
                self.scroll_lines(drag)
                self.drags_to_go %= int(self.drags_to_go)
        else:
            # When speed reaches zero, clear remaining coast
            self.drags_to_go = 0

    def end_drag(self):
        """Calculate and set drag speed."""
        time_diff = get_time() - self.drag_start_time
        if time_diff:
            self.drag_speed = (self.dragged_lines / time_diff) * DRAG_FACTOR
        self.drag_end_time = get_time()
        self.dragged_lines = 0

    def at_bottom(self):
        """Check if last line is on screen."""
        if self.new_text_list:
            return False
        return len(self.lines) <= self._get_final_line_num() + 1

    def scroll_drag(self, original_pos, current_pos):
        """Scroll based on mouse movement."""

        if not self.lines:
            return False

        y_dist = current_pos[1] - original_pos[1]
        if y_dist > 0 and self.line_num > 0:
            # Check if dragging down
            next_line = self.lines[self.line_num - 1]
        elif y_dist < 0:
            # Check if dragging up
            next_line = self.lines[self.line_num]
        else:
            return False

        next_height = next_line.height
        if abs(y_dist) >= next_height:
            line_amount = -(y_dist // abs(y_dist))  # Convert to 1/-1
            self.dragged_lines += line_amount
            self.scroll_lines(line_amount)
            return True

        return False

    def clear_all_text(self):
        """Clear all text that has been added to the box."""
        with self.text_lock:
            self.lines.clear()
            self.current_height = 0
            self.wrapped_text_list.clear()
            self.new_text_list.clear()
        _rewrap()
        _mark_dirty()

    def render(self, display: pygame.Surface, pos: List[int]):
        """Render the lines of text."""

        with self.text_lock:
            self.pos = pos
            lines_added = self._wrap_new_lines(self.was_at_bottom)

            if self.was_at_bottom and lines_added:
                # Lock scroll to bottom
                self.scroll_lines(lines_added - 1)

            line_y = self.pos[1]
            for line in self._get_lines():
                if line.height + line_y <= self.pos[1] + self.pos[3]:
                    line.set_pos((self.pos[0], line_y))
                    line.render(display)
                    line_y += line.height
                else:
                    break

            self.was_at_bottom = self.at_bottom()
        return self.was_at_bottom, self.line_num == 0


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

        self.indicator_color = DEFAULT_INDICATOR_COLOR

        self.text_wrap = _TextWrap()

        self.pos = None

        with TEXTBOX_LOCK:
            textboxes.append(self)

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
        pos = [self.pins[0] * width, self.pins[1] * height]
        pos.append(self.pins[2] * width - pos[0])
        pos.append(self.pins[3] * height - pos[1])

        self.pos = [int(x) for x in pos]

        return self.pos

    def handle_event(self, event, display):
        """Handle pygame events relating to scrolling."""

        position_based = "pos" in event.dict
        if position_based and not self.within_box(*event.pos, *get_dims(display)):
            return False

        activate_box(self)
        with self.text_wrap.text_lock:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in [4, 5]:
                    # Mouse Scroll
                    self.text_wrap._stop_coast()
                    if event.button == 4:
                        self.text_wrap.scroll_lines(-SCROLL_AMOUNT)
                    else:
                        self.text_wrap.scroll_lines(SCROLL_AMOUNT)
                elif event.button == 1:
                    # Click
                    self.text_wrap._stop_coast()
                    self.text_wrap.drag_start_time = get_time()
                    self.text_wrap.drag_start_pos = event.pos
            elif event.type == pygame.MOUSEMOTION:
                # Drag
                if not isinstance(self.text_wrap.drag_start_time, type(None)):
                    if self.text_wrap.scroll_drag(
                        self.text_wrap.drag_start_pos, event.pos
                    ):
                        self.text_wrap.drag_start_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.text_wrap.end_drag()
                    self.text_wrap.drag_start_pos = None
                    self.text_wrap.drag_start_time = None

            # Return True if event is position based to break outside loop
            return position_based

    def within_box(self, x: int, y: int, width: int, height: int) -> bool:
        """Check if given coordinates are within the box.

        Parameters
        ----------
        x
            x coordinate of point
        y
            y coordinate of point
        width
            The width of the display
        height
            The height of the display

        """
        rect = self._get_rect(width, height)
        coords = [rect[0], rect[1], rect[2] + rect[0], rect[3] + rect[1]]
        return coords[0] < x < coords[2] and coords[1] < y < coords[3]

    def _draw_box(self, display: pygame.Surface):
        """Draw the outline of the textbox to the display."""
        width = display.get_width()
        height = display.get_height()
        pos = self._get_rect(width, height)
        pygame.draw.rect(display, self.border_color, pos, self.border_width)

    def _draw_indicator(self, display: pygame.Surface, at_bottom, at_top):
        """Draw the indicator to show the box is not at the bottom."""
        width = display.get_width()
        height = display.get_height()
        pos = self._get_rect(width, height)

        if not at_bottom:
            start_pos = (pos[0], pos[1] + pos[3] - 1)
            end_pos = (pos[0] + pos[2] - 1, pos[1] + pos[3] - 1)
            pygame.draw.line(
                display, self.indicator_color, start_pos, end_pos, self.border_width + 2
            )

        if not at_top:
            start_pos = (pos[0], pos[1])
            end_pos = (pos[0] + pos[2] - 1, pos[1])
            pygame.draw.line(
                display, self.indicator_color, start_pos, end_pos, self.border_width + 2
            )

    def render(self, display: pygame.Surface):
        """Draw the textbox to the given display."""
        self._draw_box(display)
        at_bottom, at_top = self.text_wrap.render(display, self.pos)
        self._draw_indicator(display, at_bottom, at_top)


class InputBox(TextBox):
    """Allow text input and display said text."""

    def __init__(self, pins: Iterable[int]):
        TextBox.__init__(self, pins)

        self.cursor_index = 0
        self.cursor_rect = None
        self.cursor_key_press_time = None
        self.cursor_repeating = False

    def handle_event(self, event, display):
        """Handle pygame events relating to input.

        Override parent method.
        """
        within_box = TextBox.handle_event(self, event, display)

        if event.type == pygame.KEYDOWN:
            self.text_wrap._stop_coast()
            # TODO: Handle input
            if event.key in CURSOR_KEYS:
                direction = CURSOR_KEYS[event.key]
                self.move_cursor_direction(direction)

                self.cursor_key_press_time = get_time()
            else:
                key_name = pygame.key.name(event.key)
                self.insert_char(key_name)

        return within_box

    def insert_char(self, char):
        """Insert a given char at the cursor."""
        with self.text_wrap.text_lock:
            returns = self._update_cursor_pos()
            if isinstance(returns, type(None)):
                return
            line_num, text_obj, index, last_char = returns
            # TODO: Figure out remaining_chars of line segment relative to all_text in obj
            all_text = text_obj.all_text
            text = f"{all_text[:index]}{char}{all_text[index:]}"
            text_obj.change_text(text)
            self.text_wrap.mark_wrap()
            self.text_wrap._wrap_new_lines()
            self.move_cursor_chars(1)
            if last_char:
                self.move_cursor_chars(1)
        _mark_dirty()

    def move_cursor_direction(self, direction):
        """Move the cursor a given direction.
        
        Parameters
        ----------
        direction
            The direction to move the cursor. 
            "u": One line Up, "d": One line Down, INT: Left and Right
        
        """
        with self.text_wrap.text_lock:
            if isinstance(self.cursor_rect, type(None)):
                return
            if not self.text_wrap.lines:
                return
            if isinstance(direction, int):
                # Left or Right
                self.move_cursor_chars(direction)
            else:
                self.move_cursor_lines(-1 if direction == "u" else 1)

    def reset_cursor_repeat(self):
        """Reset the cursor repeat vars."""
        self.cursor_key_press_time = None
        self.cursor_repeating = False

    def handle_cursor_key(self, key):
        """Handle cursor key repeats."""
        last_press = self.cursor_key_press_time
        if self.cursor_repeating:
            if get_time() > self.cursor_key_press_time + CURSOR_REPEAT_TIME:
                self.cursor_key_press_time = get_time()
                self.move_cursor_direction(CURSOR_KEYS[key])
        elif get_time() > last_press + CURSOR_REPEAT_THRESHOLD:
            self.cursor_repeating = True
            self.cursor_key_press_time = get_time()

    def _bind_cursor(self):
        """Restrict cursor to remain within box."""
        num_chars = len(self.text_wrap.get_box_string())
        self.cursor_index = max(0, self.cursor_index)
        self.cursor_index = min(num_chars, self.cursor_index)

    def _update_cursor_pos(self, allow_scroll=True):
        """Update the box to reflect the cursor's position.
        
        Parameters
        ----------
        allow_scroll
            When true, scroll the screen to contain cursor. 
            Otherwise, change cursor index to remain on screen.

        """
        self._bind_cursor()
        while True:
            if not self.text_wrap.lines:
                self.cursor_index = 0
                self.cursor_rect = None
                return
            index = 0
            y_pos = 0
            height = 0
            found = False
            line_num = 0

            text_obj = None
            sub_index = 0
            last_char_on_line = False
            for _line_num, line in enumerate(self.text_wrap.lines):
                height = line.height
                x_pos = 0
                for text in line:
                    if text_obj != text:
                        sub_index = 0
                        text_obj = text
                    segment = line.get_text_segment(text)
                    if index + len(segment) > self.cursor_index:
                        # cursor within segment
                        remaining_chars = self.cursor_index - index
                        segment_before_cursor = segment[:remaining_chars]
                        segment_after_cursor = segment[remaining_chars:]
                        for char in segment_before_cursor:
                            if char == text.all_text[sub_index]:
                                # Determine all_text position of cursor
                                # Ignore chars not in all_text (e.g. -)
                                sub_index += 1
                        if segment_after_cursor:
                            if segment_after_cursor[0] != text.all_text[sub_index]:
                                # Next char not in all text (e.g. -)
                                last_char_on_line = True
                        x_pos += text.get_size(segment_before_cursor)[0]
                        found = True
                        break
                    x_pos += text.get_size(segment)[0]
                    index += len(segment)
                    for char in segment:
                        if char == text.all_text[sub_index]:
                            # Determine all_text position of cursor
                            # Ignore chars not in all_text (e.g. -)
                            sub_index += 1
                line_num = _line_num
                if found:
                    break
                if _line_num >= self.text_wrap.line_num:
                    y_pos += line.height
            else:
                # Not found, check past final char
                if not self.text_wrap.new_text_list:
                    # No more lines to wrap, checked everyline
                    last_line = self.text_wrap.lines[line_num]
                    y_pos -= last_line.height
                    sub_index = len(last_line.text_list[-1].all_text) - 1
                    found = True

            final_line_num = self.text_wrap._get_final_line_num()

            if not found:
                # Index not yet wrapped.
                self.text_wrap.scroll_lines(1)
                self.text_wrap._wrap_new_lines()
                continue
            elif line_num < self.text_wrap.line_num or line_num > final_line_num:
                # Cursor outside screen
                if allow_scroll:
                    lines_to_scroll = line_num - self.text_wrap.line_num
                    self.text_wrap.scroll_lines(lines_to_scroll)
                    if line_num > final_line_num:
                        y_pos -= self.text_wrap.lines[line_num - 1].height
                    else:
                        y_pos = 0
                else:
                    self._update_cursor_index()
                    break

            self.cursor_rect = [x_pos, y_pos, DEFAULT_CURSOR_WIDTH, height]
            _mark_dirty()
            break
        return line_num, text_obj, sub_index, last_char_on_line

    def get_index_from_point(self, point):
        """Determine a character index based on a given point."""

        # find line covering point
        current_height = 0
        line_num, line = 0, None
        for _line_num, _line in enumerate(self.text_wrap._get_lines()):
            current_height += _line.height
            if point[1] < current_height:
                line_num = _line_num
                line = _line
                break
        else:
            # clicked past last line
            return len(self.text_wrap.get_box_string())
        # TODO: Ensure index can go one past final char

        char_ind = 0
        current_width = 0
        for text in line:
            # Find text object covering point
            segment = line.get_text_segment(text)
            segment_width = text.get_size(segment)[0]
            current_width += segment_width
            if point[0] < current_width:
                # find char in this text object covering point
                current_width -= segment_width
                sub_segment = ""
                for _char_ind, char in enumerate(segment):
                    sub_segment += char
                    if point[0] < current_width + text.get_size(sub_segment)[0]:
                        char_ind += _char_ind
                        break
                else:
                    # On the last pixel of this text object
                    char_ind += 1
                    break
                break
            char_ind += len(segment)
        else:
            # clicked past last text object on line
            char_ind = len(line.get_line_string())

        prev_chars = 0
        # find num chars before current line
        for _line_num, line in enumerate(self.text_wrap.lines):
            if _line_num == line_num + self.text_wrap.line_num:
                break
            for text in line:
                prev_chars += len(line.get_text_segment(text))

        return prev_chars + char_ind

    def _update_cursor_index(self):
        """Determine where the cursor's index is based on it's position."""
        if isinstance(self.cursor_rect, type(None)):
            return

        point = self.cursor_rect[:2]
        index = self.get_index_from_point(point)
        if not isinstance(index, type(None)):
            self.cursor_index = index
            self._update_cursor_pos()

    def move_cursor_chars(self, num_chars):
        """Move the cursor the given number of chars left or right."""
        self.cursor_index += num_chars
        self._update_cursor_pos()

    def move_cursor_lines(self, lines):
        """Move the cursor up or down.
        
        Parameter
        ---------
        lines
            If positive, move one line down, else one line up.
            
        """
        current_line = self._update_cursor_pos()[0]
        if lines < 0:
            if current_line <= self.text_wrap.line_num:
                if current_line == 0:
                    self.cursor_index = 0
                    self._update_cursor_pos()
                else:
                    # At top of screen
                    self.text_wrap.scroll_lines(-1)
                    self._update_cursor_index()
            else:
                to_line_num = current_line - 1
                to_line = self.text_wrap.lines[to_line_num]
                self.cursor_rect[1] -= to_line.height
                self._update_cursor_index()
        elif lines > 0:
            if current_line >= self.text_wrap._get_final_line_num():
                # At bottom of screen
                self.text_wrap.scroll_lines(1)
                self.text_wrap._wrap_new_lines()
                self._update_cursor_index()
            else:
                to_line_num = current_line + 1
                to_line = self.text_wrap.lines[to_line_num]
                self.cursor_rect[1] += to_line.height
                self._update_cursor_index()

    def _draw_cursor(self, display):
        """Draw the cursor."""
        self._update_cursor_pos(False)

        self._update_cursor_index()
        if not isinstance(self.cursor_rect, type(None)):
            box_rect = self._get_rect(*get_dims(display))
            cursor_rect = self.cursor_rect[:]
            cursor_rect[0] += box_rect[0]
            cursor_rect[1] += box_rect[1]
            pygame.draw.rect(display, DEFAULT_CURSOR_COLOR, cursor_rect)

    def render(self, display):
        """Render the input box and cursor."""
        TextBox.render(self, display)
        with self.text_wrap.text_lock:
            self._draw_cursor(display)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
