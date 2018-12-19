"""Write to the display and create textboxes."""

from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Deque, Iterable, List, Optional, Set, Tuple
from itertools import islice
import time

import pygame

# Globals
RUNNING = True

# Constants
TICK = 0.01
TEXTBOX_LOCK = Lock()
TEXTBOXES = []

DEFAULT_BORDER_WIDTH = 1
DEFAULT_BORDER_COLOR = (255, 255, 255)
DEFAULT_TEXT_COLOR = (255, 255, 255)

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
mouse_down = None
mouse_time = None


def _mark_dirty():
    """Mark the display dirty (i.e. set to redraw)."""
    global DIRTY

    DIRTY = True


def _coast_scrolls():
    """Find textboxes which have coasting scrolls and perform scroll."""

    if isinstance(mouse_down, type(None)):
        for box in TEXTBOXES:
            wrap = box.text_wrap
            if wrap.drag_speed and (
                abs(wrap.drag_speed) > DRAG_DEADZONE or wrap.drags_to_go
            ):
                # Only coast if already are or above deadzone
                current_time = get_time()
                time_diff = current_time - wrap.drag_time
                wrap.drags_to_go += wrap.drag_speed * time_diff
                wrap.drag_time = current_time
                if wrap.drag_speed < 0:
                    wrap.drag_speed += DRAG_DECELERATION * time_diff
                    wrap.drag_speed = min(0, wrap.drag_speed)
                elif wrap.drag_speed > 0:
                    wrap.drag_speed -= DRAG_DECELERATION * time_diff
                    wrap.drag_speed = max(0, wrap.drag_speed)
                if abs(wrap.drags_to_go) > 1:
                    drag = int(wrap.drags_to_go)
                    wrap.scroll_lines(drag)
                    wrap.drags_to_go %= int(wrap.drags_to_go)
            else:
                # When speed reaches zero, clear remaining coast
                wrap.drags_to_go = 0


def render(display: pygame.Surface, fill_color: Iterable[int] = None):
    """Render every textbox if DIRTY."""
    global DIRTY

    _coast_scrolls()

    if DIRTY:
        if not isinstance(fill_color, type(None)):
            display.fill(fill_color)
        with TEXTBOX_LOCK:
            for textbox in TEXTBOXES:
                textbox.render(display)
        DIRTY = False


def get_time():
    """Return the current time in millis."""
    return time.time()


def _rewrap():
    """Rewrap all textboxes."""
    for textbox in TEXTBOXES:
        textbox.text_wrap.mark_wrap()


def _resize_display(size: Iterable[int]) -> pygame.Surface:
    """Resize the display to the given size."""
    _mark_dirty()
    _rewrap()
    return pygame.display.set_mode(size, pygame.VIDEORESIZE)


def get_dims(display: pygame.Surface) -> Tuple[int]:
    """Get the dimensions of the screen."""

    return display.get_width(), display.get_height()


def check_events(
    display: pygame.Surface, events: Iterable[pygame.event.Event]
) -> pygame.Surface:
    """Check pygame display events and execute accordingly."""
    global RUNNING, mouse_down, mouse_time

    for event in events:
        if event.type == pygame.QUIT:
            RUNNING = False
        elif event.type == pygame.VIDEORESIZE:
            display = _resize_display(event.dict["size"])
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button in [4, 5]:
                # Mouse Scroll
                pos = event.dict["pos"]
                for box in TEXTBOXES:
                    if box.within_box(*pos, *get_dims(display)):
                        if event.button == 4:
                            box.text_wrap.scroll_lines(-SCROLL_AMOUNT)
                        else:
                            box.text_wrap.scroll_lines(SCROLL_AMOUNT)
                        break
            elif event.button == 1:
                # Click
                mouse_down = event.dict["pos"]
                mouse_time = get_time()
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and not isinstance(mouse_time, type(None)):
                # Release
                mouse_down = None
                for box in TEXTBOXES:
                    box.text_wrap.end_drag()
        elif event.type == pygame.MOUSEMOTION:
            # Drag
            if mouse_down:
                for box in TEXTBOXES:
                    if box.within_box(*mouse_down, *get_dims(display)):
                        if box.text_wrap.scroll_drag(mouse_down, event.dict["pos"]):
                            mouse_down = event.dict["pos"]
                        break

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
    ):
        self.text_segment = text
        self.all_text = text

        self.font = font
        self.color = color
        if isinstance(color, type(None)):
            self.color = DEFAULT_TEXT_COLOR
        self.highlight = highlight

        self.new_line = new_line

        self.original_font_repr = repr(self.font)
        self.pos = None

    def set_pos(self, pos: Iterable[int]):
        """Set the Text's pos."""
        self.pos = pos

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

    def render(self, display: pygame.Surface):
        """Render the line to the display."""
        text_x = 0
        for text in self.text_list:
            text_id = id(text)
            if text_id in self.text_segments:
                text_segment = self.text_segments[text_id]
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

    # TODO: Add hover word support at display level
    #   Easiest way to ensure hover text stays with correct words
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
        self.drag_time = None
        self.dragged_lines = 0
        self.drags_to_go = 0

    def _next_line(self):
        """Get the next line to be filled."""
        if self.lines:
            line = self.lines.pop()
            self.current_height -= line.height
        else:
            line = _Line()
        return line

    def _wrap_new_lines(self):
        """Wrap text into lines."""

        def text_needs_wrapped():
            """Check if text still needs wrapped."""
            return self.new_text_list

        def within_height():
            """Check if the current wrapped lines are shorter than height of box."""
            return self.current_height < self.pos[3]

        lines_added = 0

        if text_needs_wrapped() and within_height():
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

                if self.current_height + line.height > self.pos[3]:
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
        self._stop_coast()
        with self.text_lock:
            self.lines.clear()
            self.current_height = 0
            # Move old lines back into
            self._purge_segments()
            self.wrapped_text_list.reverse()
            self.new_text_list.extendleft(self.wrapped_text_list)
            self.wrapped_text_list.clear()
            self.line_num = 0
            self.remaining_segments.clear()

    def add_text(self, text_list: Iterable[Text]):
        """Add text to the current input."""
        with self.text_lock:
            self.new_text_list.extend(text_list)
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
        with self.text_lock:
            self.line_num += num_lines
            self.line_num = max(0, self.line_num)
            self.calculate_height()
            _mark_dirty()

    def _stop_coast(self):
        """Stop coasting."""
        self.drag_speed = 0
        self.drag_time = None
        self.dragged_lines = 0
        self.drags_to_go = 0

    def end_drag(self):
        """Calculate and set drag speed."""
        time_diff = get_time() - mouse_time
        if time_diff:
            self.drag_speed = (self.dragged_lines / time_diff) * DRAG_FACTOR
        self.drag_time = get_time()
        self.dragged_lines = 0

    def at_bottom(self):
        """Check if last line is on screen."""
        return len(self.lines) == self._get_final_line_num() + 1

    def scroll_drag(self, original_pos, current_pos):
        """Scroll based on mouse movement."""

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
            at_bottom = self.at_bottom() and self.lines
            lines_added = self._wrap_new_lines()

        to_scroll = len(self.lines) - self.line_num - 1
        if to_scroll < 0:
            # Ensure we don't scroll past the last line
            self.scroll_lines(to_scroll)

        if at_bottom and lines_added:
            # Lock scroll to bottom
            self.scroll_lines(lines_added - 1)

        self._wrap_new_lines()

        with self.text_lock:
            line_y = self.pos[1]
            for line in self._get_lines():
                if line.height + line_y <= self.pos[1] + self.pos[3]:
                    line.set_pos((self.pos[0], line_y))
                    line.render(display)
                    line_y += line.height
                else:
                    break


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
        pos = [self.pins[0] * width, self.pins[1] * height]
        pos.append(self.pins[2] * width - pos[0])
        pos.append(self.pins[3] * height - pos[1])

        self.pos = [int(x) for x in pos]

        return self.pos

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
