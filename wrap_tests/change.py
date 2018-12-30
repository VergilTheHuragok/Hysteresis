"""Wrap text that changes randomly.

Must be ran from root of project.
"""
from time import sleep
import random
import string

from interface.display import InputBox, Text, Font
import interface.start

interface.start.init()

font1 = Font("Courier New", 20, True, True)

y = InputBox([.1, .1, .9, .9])
y.text_wrap.add_text([Text("Changing", font1, highlight=(255, 125, 125), label="main")])
y.text_wrap.add_text([Text("Unchanged", font1, highlight=(125, 255, 125))])

while interface.start.get_running():
    text = (
        "".join(
            random.choice(string.printable)
            for i in range(0, random.randint(1, 50))
        )
    )
    y.text_wrap.change_text("main", text)
    sleep(3)
