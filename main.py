"""Start the game."""
from time import sleep

from interface.display import TextBox, InputBox
import interface.start

interface.start.init()

TextBox([0, .1, .7, .5])
TextBox([.3, .3, .6, 1])
InputBox([0, 0, 1, 1])

while interface.start.get_running():
    sleep(.01)
