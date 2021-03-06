"""Test scrolling.

Must be ran from root of project.
"""
from time import sleep
import random
import _thread

from interface.display import TextBox, Text, Font
import interface.start

from wrap_tests.block import get_text

interface.start.init()

font1 = Font("Courier New", 20, True, True)

y = TextBox([0.1, 0.1, 0.9, 0.9])

for line in get_text().split("\n"):
    y.text_wrap.add_text([Text(line, font1, new_line=True)])
scroll = []


def new_thread():
    _thread.start_new_thread(lambda: scroll.append(input()), ())


new_thread()

while interface.start.get_running():
    if scroll:
        amount = scroll.pop()
        if amount == "":
            amount = random.randint(-5, 5)
        amount = int(amount)
        new_thread()
        y.text_wrap.scroll_lines(amount)
    sleep(.01)