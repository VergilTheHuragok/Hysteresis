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

y.text_wrap.add_text([Text(get_text(), font1)])
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
        mult = 1
        if amount < 0:
            mult = -1
        for i in range(0, abs(amount)):
            y.text_wrap.scroll_lines(mult)
            sleep(.1)
    sleep(.01)