"""Wrap a paragraph of text.

Must be ran from root of project.
"""
from time import sleep

from interface.display import TextBox, Text, Font
import interface.start

interface.start.init()

font1 = Font("Courier New", 20, True, True)

text = """
This block of text goes on and on and does not have any visual separation between what would normally make up a new paragraph. Instead, it will continue to have more text added to it and look like it has not been formatted. It just keeps going and going and going and will start new topics without separating them with paragraphs. You see, even though this is nice, let's talk about Cascading Style Sheets (CSS), oftentimes called style sheets, for a minute. Style sheets are often used to affect the appearance of Web pages. CSS code contains selectors and definitions for the various tags, classes, or ids that are used when marking up and HTML document. JavaScript, on the other hand, can add additional functionality to a Web page. Since it is a programming language, you can write code to perform any number of tasks. You could change the content within a block of text, change an image when the user places their mouse over a specific part of the page, validate form content, send alert messages, and more. It can be learned through books, tutorials, or classes that are offered in many place, especially on the Web. If you want to delve into server-side programming, you might look into PHP, ASP, Perl, Java, or a number of other available languages. These allow to save information into databases, handle feedback forms, create shopping carts, and more. Did you read all of this or did you give up after trying for a bit?
"""  # BUG: Text repeats at end

x = TextBox([.1, .1, .45, .9])
y = TextBox([.55, .1, .9, .9])

for char in text:
    x.text_wrap.add_text([Text(char, font1)])
y.text_wrap.add_text([Text(text, font1)])


while interface.start.get_running():
    sleep(.01)
