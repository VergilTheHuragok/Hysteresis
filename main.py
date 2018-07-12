"""Start the game."""
from time import sleep

from interface.display import TextBox, InputBox, Text, Font
import interface.start

interface.start.init()

font1 = Font("Comic Sans", 50, True, True)

x = TextBox([0, .1, .7, .5])
y = TextBox([.3, .3, .6, 1])
# InputBox([0, 0, 1, 1])

for i in range(0, 1000):
    x.add_text([Text(str(i), font1, (255, 0, 255), (0, 0, 255))])
    y.add_text([Text(str(i), font1, highlight=(255, 0, 255))])

# BUG: Occasionally freezes on launch with no changes
#      Due to screen resizing right at start?

while interface.start.get_running():
    sleep(.01)
