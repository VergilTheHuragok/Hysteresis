"""Wrap a paragraph of text with new_lines.

Must be ran from root of project.
"""
from time import sleep
import random

from interface.display import TextBox, Text, Font
import interface.start

interface.start.init()

font1 = Font("Courier New", 20, True, True)

text = """
The Hitchhiker's Guide to the Galaxy[1] (sometimes referred to as HG2G,[2] HHGTTG[3] or H2G2[4]) is a comedy science fiction series created by Douglas Adams. Originally a radio comedy broadcast on BBC Radio 4 in 1978, it was later adapted to other formats, including stage shows, novels, comic books, a 1981 TV series, a 1984 video game, and 2005 feature film.

A prominent series in British popular culture, The Hitchhiker's Guide to the Galaxy has become an international multi-media phenomenon; the novels are the most widely distributed, having been translated into more than 30 languages by 2005.[5][6] In 2017, BBC Radio 4 announced a 40th-anniversary celebration with Dirk Maggs, one of the original producers, in charge.[7] This sixth series of the sci-fi spoof has been based on Eoin Colfer's book And Another Thing, with additional unpublished material by Douglas Adams. The first of six new episodes was broadcast on 8 March 2018.[8]

The broad narrative of Hitchhiker follows the misadventures of the last surviving man, Arthur Dent, following the demolition of the planet Earth by a Vogon constructor fleet to make way for a hyperspace bypass. Dent is rescued from Earth's destruction by Ford Prefect, a human-like alien writer for the eccentric, electronic travel guide The Hitchhiker's Guide to the Galaxy, by hitchhiking onto a passing Vogon spacecraft. Following his rescue, Dent explores the galaxy with Prefect and encounters Trillian, another human that had been taken from Earth prior to its destruction by the President of the Galaxy, the two-headed Zaphod Beeblebrox, and the depressed Marvin, the Paranoid Android. Certain narrative details were changed between the various adaptations.

"""

x = TextBox([.1, .1, .45, .9])
y = TextBox([.55, .1, .9, .9])

string = ''
for i, char in enumerate(text):
    string += char
    if not i % 40 or i == len(text) - 1:
        color = tuple(random.randint(0, 255) for _ in range(0, 3))
        x.text_wrap.add_text([Text(string, font1, highlight=color, new_line=True)])
        y.text_wrap.add_text([Text(string, font1, highlight=color)])
        string = ''

while interface.start.get_running():
    sleep(.01)
