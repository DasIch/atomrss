"""
    atomrss.rss
    ~~~~~~~~~~~

    This is an implementation of a RSS 2.0 parser based on version 2.0.11 of
    the RSS 2.0 specification_.

    .. _specification: http://www.rssboard.org/rss-2-0-11

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import logging
import email.utils

import lxml.etree
import structlog
import structlog.stdlib
import dateutil.parser

from atomrss.exceptions import ParserError


SUPPORTED_VERSIONS = {'2.0', '0.92', '0.91'}


logger = structlog.get_logger(
    logging.getLogger('atomrss.rss'),
    wrapper_class=structlog.stdlib.BoundLogger
)


class RSS:
    def __init__(self, version, channel):
        #: The RSS version.
        self.version = version

        #: The :class:`Channel` instance.
        self.channel = channel


class Channel:
    def __init__(self, title, link, description, items):
        #: The title of the channel.
        self.title = title

        #: A link to the website corresponding to the channel.
        self.link = link

        #: A description of the channel.
        self.description = description

        #: A list of :class:`Item` instances.
        self.items = items


class Item:
    def __init__(self, title=None, link=None, description=None,
                 author=None,
                 pub_date=None,
                 enclosure=None):
        #: An optional title for this item. Either the title or the
        #: :attr:`description` is always present.
        self.title = title

        #: An optional link to a website corresponding to the item.
        self.link = link

        #: An optional description for the item. This may be a synopsis or the
        #: the entire content of the item. Either the description or the
        #: :attr:`title` is always present.
        self.description = description

        #: An optional :class:`Person` instance corresponding to the author of
        #: the item.
        self.author = author

        #: An optional publication date for the item.
        self.pub_date = pub_date

        #: An optional :class:`Enclosure` instance. This is used to enclose
        #: files such as mp3s in case of podcasts.
        self.enclosure = enclosure


class Person:
    def __init__(self, name, email):
        #: The name of the person.
        self.name = name

        #: An email address associated with the person.
        self.email = email


class Enclosure:
    def __init__(self, url, length, type):
        #: The URL of the enclosed file.
        self.url = url

        #: The length of the enclosed file in bytes.
        self.length = length

        #: The MIME type of the enclosed file.
        self.type = type


class RSSParserError(ParserError):
    pass


class MissingElement(RSSParserError):
    pass


class MissingAttribute(RSSParserError):
    pass


class InvalidRoot(MissingElement):
    pass


class VersionNotSupported(RSSParserError):
    pass


def parse(source, parser=None):
    tree = lxml.etree.parse(source, parser=parser)
    return parse_tree(tree)


def parse_tree(tree):
    parser = _Parser(tree)
    return parser.parse()


class _Parser:
    def __init__(self, tree):
        self.tree = tree

        self.logger = logger.bind(source=self.tree.docinfo.URL)

    def parse(self):
        return self.parse_rss()

    def parse_rss(self):
        element = self.tree.getroot()
        if element.tag != 'rss':
            raise InvalidRoot(
                '<{}>'.format(element.tag),
                lineno=element.sourceline
            )
        if 'version' in element.attrib:
            version = element.attrib['version']
            if version not in SUPPORTED_VERSIONS:
                raise VersionNotSupported(version)
        else:
            raise MissingAttribute(
                '<rss> is missing a version attribute',
                lineno=element.sourceline
            )
        self.logger = self.logger.bind(rss_version=version)
        return RSS(version, self.parse_channel())

    def parse_channel(self):
        element = self.tree.find('channel')
        if element is None:
            raise MissingElement('<channel>', self.tree.getroot().sourceline)

        title = self._get_element_text(element, 'title')
        link = self._get_element_text(element, 'link')
        description = self._get_element_text(element, 'description')

        # TODO: Add support for:
        #       * language
        #       * copyright
        #       * managingEditor
        #       * webMaster
        #       * lastBuildDate
        #       * category
        #       * generator
        #       * docs
        #       * cloud
        #       * ttl
        #       * image
        #       * rating
        #       * textInput
        #       * skipHours
        #       * skipDays

        items = [
            item
            for item in map(self.parse_item, element.findall('item'))
            if item is not None
        ]

        return Channel(title, link, description, items)

    def parse_item(self, element):
        title = self._get_element_text(element, 'title', default=None)
        link = self._get_element_text(element, 'link', default=None)
        description = self._get_element_text(element, 'description', default=None)

        if title is None and description is None:
            self.logger.error(
                'invalid-item',
                cause='element-missing',
                lineno=element.sourceline
            )
            return

        # TODO: Add support for:
        #       * category
        #       * comments
        #       * enclosure
        #       * guid
        #       * source

        return Item(
            title, link, description,
            author=self.parse_item_author(element),
            pub_date=self.parse_item_pub_date(element),
            enclosure=self.parse_item_enclosure(element)
        )

    def parse_item_author(self, item):
        email_address = self._get_element_text(item, 'author', default=None)
        if email_address is None:
            return

        return Person(*email.utils.parseaddr(email_address))

    def parse_item_pub_date(self, item):
        pub_date = item.find('pubDate')
        if pub_date is None:
            return

        try:
            return dateutil.parser.parse(pub_date.text)
        except (ValueError, OverflowError):
            self.logger.error(
                'invalid-pub-date',
                date=pub_date.text,
                lineno=pub_date.sourceline
            )
            return

    def parse_item_enclosure(self, item):
        element = item.find('enclosure')
        if element is None:
            return

        try:
            url = element.attrib['url']
            raw_length = element.attrib['length']
            type = element.attrib['type']
        except KeyError as error:
            self.logger.error(
                'invalid-enclosure',
                cause='missing-attribute',
                attribute=error.args[0],
                lineno=element.sourceline
            )
            return

        try:
            length = int(raw_length)
            if length < 0:
                raise ValueError('invalid length')
        except ValueError as error:
            self.logger.error(
                'invalid-enclosure',
                cause='invalid-length',
                length=raw_length,
                lineno=element.sourceline
            )

        return Enclosure(url, length, type)

    def _get_element_text(self, tree, name, **kwargs):
        missing = object()
        default = kwargs.pop('default', missing)
        if kwargs:
            argument = kwargs.popitem()[0]
            raise TypeError(
                'got an unexpected keyword argument {!r}'.format(argument)
            )

        element = tree.find(name)
        if element is None:
            if default is missing:
                raise MissingElement('<{}>'.format(name))
            return default
        return element.text
