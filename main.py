"""Start the game."""
from time import sleep
import string
import random

from interface.display import TextBox, InputBox, Text, Font
import interface.start

interface.start.init()

font1 = Font("Courier New", 50, True, True)

x = TextBox([.1, .1, .45, .9])
y = TextBox([.55, .1, .9, .9])
# InputBox([0, 0, 1, 1])

for i in range(0, 100):
    x.text_wrap.add_text([Text(str(i) + ', ', font1, (255, 255, 255))])

y.text_wrap.add_text([Text(''.join(random.choice(string.printable) for i in range(0, 100)), font1, highlight=(255, 0, 255))])
    
while interface.start.get_running():
    sleep(.01)
