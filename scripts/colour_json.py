import json

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JsonLexer


def print_json_in_colour(json_data, colour=True):
    json_str = json.dumps(json_data, indent=4, sort_keys=True)
    if colour:
        print(highlight(json_str, JsonLexer(), TerminalFormatter()))
    else:
        print(json_str)
