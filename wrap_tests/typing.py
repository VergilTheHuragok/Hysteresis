"""Wrap a blank input box.

Must be ran from root of project.
"""
from time import sleep

from interface.display import InputBox, Font, Text
import interface.start

interface.start.init()

font1 = Font("Courier New", 20, True, True)

x = InputBox([.1, .1, .9, .9])
x.text_wrap.add_text([Text("", font1)])

while interface.start.get_running():
    sleep(.01)
