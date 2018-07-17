"""Wrap and display all chars.

Must be ran from root of project.
"""
from time import sleep
import string
import random

from interface.display import TextBox, Text, Font
import interface.start

interface.start.init()

font1 = Font("Courier New", 50, True)


y = TextBox([.1, .1, .9, .9])

for i in range(0, 100):
    color = tuple(random.randint(0, 255) for _ in range(0, 3))
    text = string.printable * 1000
    y.text_wrap.add_text([Text(text, font1, highlight=color)])

while interface.start.get_running():
    sleep(.01)
