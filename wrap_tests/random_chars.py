"""Wrap and display random chars.

Must be ran from root of project.
"""
from time import sleep
import string
import random

from interface.display import TextBox, Text, Font
import interface.start

interface.start.init()

font1 = Font("Courier New", 50, True)


x = TextBox([.1, .1, .45, .9])
y = TextBox([.55, .1, .9, .9])

for i in range(0, 100):
    color = tuple(random.randint(0, 255) for _ in range(0, 3))
    text = ("".join(random.choice(string.printable) for i in range(0, 10))).replace(
        "\n", ""
    )
    x.text_wrap.add_text([Text(char, font1, highlight=color) for char in text])
    y.text_wrap.add_text([Text(text, font1, highlight=color)])

while interface.start.get_running():
    sleep(.01)
