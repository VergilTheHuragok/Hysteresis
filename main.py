"""Start the game."""
from time import sleep

from interface.display import TextBox
import interface.start

interface.start.init()

TextBox([0, .1, .7, .5])
TextBox([.3, .3, .6, 1])

while interface.display.running:
    sleep(.01)