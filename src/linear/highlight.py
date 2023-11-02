import textwrap

import pygments
from pygments.formatters import TerminalFormatter
from pygments.lexers.markup import MarkdownLexer


def wrap_text(text: str, width: int = 88, break_long_words: bool = False) -> str:
    """
    Wraps the input text to the specified width.

    Args:
        text: The text to wrap.
        width: The width to wrap to.
        break_long_words: If true, long words will be broken.

    Returns:
        The wrapped text.
    """
    lines = text.split("\n")
    wrapped_lines = [
        textwrap.fill(line, width=width, break_long_words=break_long_words)
        for line in lines
    ]
    wrapped_text = "\n".join(wrapped_lines)
    return wrapped_text


def markdown(text: str, wrap: bool = False):
    """
    Highlights the markdown syntax in the input text.

    Args:
        text: The text to highlight.
        wrap: If true, the text will be wrapped to 88 characters.

    Returns:
        The highlighted text.
    """
    if wrap:
        text = wrap_text(text)

    return pygments.highlight(text, MarkdownLexer(), TerminalFormatter())
