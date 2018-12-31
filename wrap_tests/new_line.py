"""Wrap a paragraph of text with new_lines.

Must be ran from root of project.
"""
from time import sleep
import random

from interface.display import InputBox, Text, Font
import interface.start

interface.start.init()

font1 = Font("Courier New", 20, True, True)

text = """
For all its material advantages, the sedentary life has left us edgy, unfulfilled. Even after 400 generations in villages and cities, we haven’t forgotten. The open road still softly calls, like a nearly forgotten song of childhood. We invest far-off places with a certain romance. This appeal, I suspect, has been meticulously crafted by natural selection as an essential element in our survival. Long summers, mild winters, rich harvests, plentiful game—none of them lasts forever. It is beyond our powers to predict the future. Catastrophic events have a way of sneaking up on us, of catching us unaware. Your own life, or your band’s, or even your species’ might be owed to a restless few—drawn, by a craving they can hardly articulate or understand, to undiscovered lands and new worlds.

Herman Melville, in Moby Dick, spoke for wanderers in all epochs and meridians: “I am tormented with an everlasting itch for things remote. I love to sail forbidden seas…”

Maybe it’s a little early. Maybe the time is not quite yet. But those other worlds— promising untold opportunities—beckon.

Silently, they orbit the Sun, waiting.
"""

x = InputBox([.1, .1, .45, .9])
y = InputBox([.55, .1, .9, .9])

string = ""
for i, char in enumerate(text):
    string += char
    if not i % 40 or i == len(text) - 1:
        color = tuple(random.randint(0, 255) for _ in range(0, 3))
        x.text_wrap.add_text([Text(string, font1, highlight=color, new_line=True)])
        y.text_wrap.add_text([Text(string, font1, highlight=color)])
        string = ""

while interface.start.get_running():
    sleep(.01)
