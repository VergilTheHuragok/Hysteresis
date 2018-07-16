"""Wrap random text with random fonts.

Must be ran from root of project.
"""
from time import sleep
import random
import string

from interface.display import TextBox, Text, Font
import interface.start

interface.start.init()

font1 = Font("Courier New", 20, True, True)

x = TextBox([.1, .1, .45, .9])
y = TextBox([.55, .1, .9, .9])


while interface.start.get_running():
    for i in range(0, random.randint(1, 15)):
        color = tuple(random.randint(0, 255) for _ in range(0, 3))
        text = (''.join(random.choice(string.printable) for i in range(0, random.randint(1, 100)))).replace("\n", '')
        
        x_text_list = []
        font2 = font1.edit(size=random.randint(1, 100))
        for char in text:
            text_object = Text(char, font1, highlight=color)
            text_object.set_font(font2)
            x_text_list.append(text_object)

        x.text_wrap.add_text(x_text_list)
        y.text_wrap.add_text([Text(text, font2, highlight=color)])
    sleep(.001)
    x.text_wrap.clear_all_text()
    y.text_wrap.clear_all_text()
