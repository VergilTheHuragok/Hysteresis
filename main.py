"""Start the game."""
from time import sleep

import display
from display import TextBox

display.init()

TextBox([0, .1, .7, .5])
TextBox([.3, .3, .6, 1])

while display.running:
    sleep(.01)