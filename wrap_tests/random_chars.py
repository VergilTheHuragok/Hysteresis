"""Wrap and display random chars.

Must be ran from root of project.
"""
from time import sleep
import string
import random
import _thread

from interface.display import TextBox, Text, Font
import interface.start

interface.start.init()

font1 = Font("Courier New", 50, True)


x = TextBox([0.1, 0.1, 0.45, 0.9])
y = TextBox([0.55, 0.1, 0.9, 0.9])


def add_text():
    color = tuple(random.randint(0, 255) for _ in range(0, 3))
    text = (
        "".join(
            random.choice(string.printable + string.ascii_letters * 3)
            for i in range(0, random.randint(1, 100))
        )
    ).replace("\n", "")
    x.text_wrap.add_text([Text(char, font1, highlight=color) for char in text])
    y.text_wrap.add_text([Text(text, font1, highlight=color)])


while interface.start.get_running():
    add_text()

    sleep(.1)
