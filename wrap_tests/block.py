"""Test a single large block of text with newlines as seperate text objects

Must be ran from root of project.
"""
from time import sleep

from interface.display import TextBox, Text, Font
import interface.start

from requests_html import HTMLSession
from bs4 import BeautifulSoup
from bs4.element import Comment


def tag_visible(element):
    """https://stackoverflow.com/a/1983219/7587147"""
    if element.parent.name in [
        "style",
        "script",
        "head",
        "title",
        "meta",
        "[document]",
    ]:
        return False
    if isinstance(element, Comment):
        return False
    return True


def text_from_html(body):
    """https://stackoverflow.com/a/1983219/7587147"""
    soup = BeautifulSoup(body, "html.parser")
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    return u" ".join(t.strip() for t in visible_texts)


session = HTMLSession()
r = session.get("https://rifters.com/real/STARFISH.htm")
text = r.text

interface.start.init()

font1 = Font("Courier New", 20, True, True)

y = TextBox([0.1, 0.1, 0.9, 0.9])
for line in text_from_html(text).split("\n"):
    y.text_wrap.add_text([Text(line, font1, new_line=True)])


while interface.start.get_running():
    sleep(0.01)
