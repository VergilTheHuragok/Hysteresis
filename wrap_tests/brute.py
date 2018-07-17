"""Wrap random text with random fonts.

Must be ran from root of project.
"""
from time import sleep
import random
import string

from interface.display import TextBox, Text, Font
import interface.start

interface.start.init()

font1 = Font("Courier New", 20, True, True)

y = TextBox([.1, .1, .9, .9])

while interface.start.get_running():
    for i in range(0, random.randint(1, 15)):
        color = tuple(random.randint(0, 255) for _ in range(0, 3))
        text = (
            "".join(
                random.choice(string.printable)
                for i in range(0, random.randint(1, 100))
            )
        ).replace("\n", "")

        font2 = font1.edit(size=random.randint(1, 250))
        y.text_wrap.add_text([Text(text, font2, highlight=color)])
    sleep(.001)
    y.text_wrap.clear_all_text()
