"""
    atomrss.exceptions
    ~~~~~~~~~~~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""


class ParserError(Exception):
    """
    Represents an error that occurred while parsing a feed.
    """

    def __init__(self, message, lineno=None):
        if lineno is not None:
            message = '{} (line: {})'.format(message, lineno)
        super().__init__(message)
        self.lineno = lineno
