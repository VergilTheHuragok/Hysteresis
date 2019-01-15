"""Start the game."""
from time import sleep

from interface.display import InputBox, Font, Text
import interface.start

interface.start.init()

font1 = Font("Courier New", 20, True, True)

x = InputBox([0.1, 0.1, 0.9, 0.9])
x.text_wrap.add_text([Text("", font1)])

while interface.start.get_running():
    sleep(0.01)
