import pygments
from pygments.formatters import TerminalFormatter
from pygments.lexers.markup import MarkdownLexer


def markdown(text: str) -> str:
    """
    Highlights the markdown syntax in the input text.

    Args:
        text: The text to highlight.
        wrap: If true, the text will be wrapped to 88 characters.

    Returns:
        The highlighted text.
    """
    return pygments.highlight(text, MarkdownLexer(), TerminalFormatter())
