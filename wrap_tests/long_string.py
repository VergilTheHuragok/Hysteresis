"""Wrap a long string of text.

Must be ran from root of project.
"""
from time import sleep

import string

from interface.display import InputBox, Text, Font
import interface.start

interface.start.init()

font1 = Font("Courier New", 20, True, True)


text = "0123456789" * 100

y = InputBox([.1, .1, .9, .9])
y.text_wrap.add_text([Text(text, font1)])


while interface.start.get_running():
    sleep(.01)
