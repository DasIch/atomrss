"""
    atomrss.atom
    ~~~~~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import html
import logging
from collections import namedtuple

import structlog
import structlog.stdlib
import lxml.etree
import dateutil.parser

from atomrss.exceptions import ParserError


ATOM_NAMESPACE = 'http://www.w3.org/2005/atom'
XHTML_NAMESPACE = 'http://www.w3.org/1999/xhtml'


DEFAULT_LOGGER = structlog.wrap_logger(
    logging.getLogger(__name__),
    wrapper_class=structlog.stdlib.BoundLogger
)


class Feed:
    def __init__(self, id, title, updated, entries,
                 authors=None,
                 contributors=None,
                 subtitle=None,
                 links=None):
        self.id = id
        self.title = title
        self.updated = updated
        self.entries = entries

        self.authors = [] if authors is None else authors
        self.contributors = [] if contributors is None else contributors
        self.subtitle = subtitle
        self.links = [] if links is None else links


class Entry:
    def __init__(self, id, title, updated,
                 authors=None,
                 contributors=None,
                 published=None,
                 summary=None,
                 links=None,
                 content=None):
        self.id = id
        self.title = title
        self.updated = updated

        self.authors = [] if authors is None else authors
        self.contributors = [] if contributors is None else contributors
        self.published = published
        self.summary = summary
        self.links = [] if links is None else links
        self.content = content


class Link:
    def __init__(self, href, rel='alternate', type=None, hreflang=None,
                 title=None, length=None):
        #: An IRI reference.
        self.href = href

        #: A relation type indicating how the linked resource relates to the
        #: feed or entry containing the link.
        self.rel = rel

        #: A hint indicating the media type of the linked resource.
        self.type = type

        #: An optional indication of linked contents language. In combination
        #: `rel='alternate'` indicates a translation.
        self.hreflang = hreflang

        #: Optional human-readable information about the link.
        self.title = title

        #: An optional indication of the linked content's length in bytes.
        self.length = length

    def __eq__(self, other):
        if isinstance(other, Link):
            return (
                self.href == other.href and
                self.rel == other.rel and
                self.type == other.type and
                self.hreflang == other.hreflang and
                self.title == other.title and
                self.length == other.length
            )
        return NotImplemented

    def __repr__(self):
        return '{}({!r}, rel={!r}, type={!r}, hreflang={!r}, title={!r}, length={!r})'.format(
            self.__class__.__qualname__,
            self.href, self.rel, self.type, self.hreflang, self.title, self.length
        )


Text = namedtuple('Text', ['type', 'value'])


Person = namedtuple('Person', ['name', 'uri', 'email'])


Content = namedtuple('Content', ['type', 'src', 'value'])


class AtomParserError(ParserError):
    def to_log_kwargs(self):
        return {
            'event': self.args[0],
            'lineno': self.lineno
        }


class NotImplementedError(AtomParserError):
    def to_log_kwargs(self):
        return {
            'event': 'not-implemented-error',
            'feature': self.args[0],
            'lineno': self.lineno
        }


class MissingElement(AtomParserError):
    def to_log_kwargs(self):
        return {
            'event': 'missing-element',
            'element': self.args[0],
            'lineno': self.lineno
        }


class InvalidRoot(MissingElement):
    pass


class InvalidDate(AtomParserError):
    def __init__(self, date, lineno=None):
        super().__init__(date, lineno=lineno)
        self.date = date

    def to_log_kwargs(self):
        return {
            'event': 'invalid-date',
            'date': self.date,
            'lineno': self.lineno
        }


def parse(source, logger=None):
    tree = lxml.etree.parse(source)
    return parse_tree(tree, logger=logger)


def parse_tree(tree, logger=None):
    return _Parser(tree, logger=logger).parse()


class _Parser:
    def __init__(self, tree, logger=None):
        self.tree = tree

        if logger is None:
            logger = DEFAULT_LOGGER
        self.logger = logger.bind(source=self.tree.docinfo.URL)
        self.namespace = ATOM_NAMESPACE

    def create_name(self, name):
        return lxml.etree.QName(self.namespace, name)

    def parse(self):
        # Figure out the namespace in the case used in the XML file.
        root = self.tree.getroot()
        for namespace in root.nsmap.values():
            if namespace.lower() == self.namespace:
                self.namespace = namespace
                break

        return self.parse_feed()

    def parse_feed(self):
        element = self.tree.getroot()
        if element.tag != self.create_name('feed'):
            raise InvalidRoot(
                '<{}>'.format(element.tag),
                lineno=element.sourceline
            )

        id = self.parse_id(element)
        title = self.parse_title(element)
        updated = self.parse_updated(element)
        entries = self.parse_entries(element)

        return Feed(
            id, title, updated, entries,
            authors=self.parse_authors(element),
            contributors=self.parse_contributors(element),
            subtitle=self.parse_subtitle(element),
            links=self.parse_links(element)
        )

    def parse_entries(self, tree):
        name = self.create_name('entry')
        return [
            entry
            for entry in map(self.parse_entry, tree.findall(name))
            if entry is not None
        ]

    def parse_entry(self, element):
        try:
            id = self.parse_id(element)
            title = self.parse_title(element)
            updated = self.parse_updated(element)
        except AtomParserError as err:
            kwargs = err.to_log_kwargs()
            kwargs['cause'] = kwargs['event']
            kwargs['event'] = 'invalid-entry'
            self.logger.error(**kwargs)
            return

        return Entry(
            id, title, updated,
            authors=self.parse_authors(element),
            contributors=self.parse_contributors(element),
            published=self.parse_published(element),
            summary=self.parse_summary(element),
            links=self.parse_links(element),
            content=self.parse_content(element)
        )

    def parse_id(self, tree):
        name = self.create_name('id')
        return self._get_element_text(tree, name)

    def parse_title(self, tree):
        name = self.create_name('title')
        element = tree.find(name)
        if element is None:
            raise MissingElement(
                '<atom:{}>'.format(name.localname),
                lineno=tree.sourceline
            )
        return self.parse_text_construct(element)

    def parse_updated(self, tree):
        name = self.create_name('updated')
        element = tree.find(name)
        if element is None:
            raise MissingElement(
                '<atom:{}>'.format(name.localname),
                lineno=tree.sourceline
            )

        try:
            return dateutil.parser.parse(element.text)
        except (ValueError, OverflowError):
            raise InvalidDate(element.text, lineno=element.sourceline)

    def parse_authors(self, tree):
        name = self.create_name('author')
        return list(
            filter(None, map(self.parse_person_construct, tree.findall(name)))
        )

    def parse_contributors(self, tree):
        name = self.create_name('contributor')
        return list(
            filter(None, map(self.parse_person_construct, tree.findall(name)))
        )

    def parse_published(self, tree):
        name = self.create_name('published')
        element = tree.find(name)
        if element is None:
            return
        try:
            return self.parse_date_construct(element)
        except InvalidDate as err:
            kwargs = err.to_log_kwargs()
            kwargs['cause'] = kwargs['event']
            kwargs['event'] = 'invalid-published'
            self.logger.error(**kwargs)
            return

    def parse_summary(self, tree):
        name = self.create_name('summary')
        element = tree.find(name)
        if element is None:
            return
        try:
            return self.parse_text_construct(element)
        except NotImplementedError as err:
            self.logger.error(*err.to_log_kwargs())
            return

    def parse_subtitle(self, tree):
        name = self.create_name('subtitle')
        element = tree.find(name)
        if element is None:
            return
        return self.parse_text_construct(element)

    def parse_links(self, tree):
        name = self.create_name('link')
        return list(
            filter(None, map(self.parse_link, tree.findall(name)))
        )

    def parse_link(self, element):
        try:
            href = element.attrib['href']
        except KeyError:
            self.logger.error(
                'invalid-link',
                cause='missing-attribute',
                attribute='href',
                lineno=element.sourceline
            )
            return

        return Link(
            href,
            rel=element.attrib.get('rel', 'alternate'),
            type=element.attrib.get('type'),
            hreflang=element.attrib.get('hreflang'),
            title=element.attrib.get('title'),
            length=element.attrib.get('length')
        )

    def parse_content(self, tree):
        name = self.create_name('content')
        element = tree.find(name)
        if element is None:
            return

        src = element.attrib.get('src')
        type = element.attrib.get('type', 'text')
        if type in {'text', 'html', 'xhtml'}:
            try:
                value = self.parse_text_construct(element).value
            except AtomParserError as err:
                self.logger.error(*err.to_log_kwargs())
                return
        return Content(type, src, value)

    def parse_text_construct(self, element):
        type = element.attrib.get('type', 'text')
        if type == 'xhtml':
            raise NotImplementedError(
                'xhtml text construct',
                lineno=element.sourceline
            )
        elif type == 'html':
            value = html.unescape(element.text)
        else:
            value = element.text
        return Text(type, value)

    def parse_person_construct(self, element):
        name = self._get_element_text(element, self.create_name('name'))
        try:
            uri = self._get_element_text(element, self.create_name('uri'))
        except MissingElement:
            uri = None
        try:
            email = self._get_element_text(element, self.create_name('email'))
        except MissingElement:
            email = None
        return Person(name, uri, email)

    def parse_date_construct(self, element):
        try:
            return dateutil.parser.parse(element.text)
        except (ValueError, OverflowError):
            raise InvalidDate(element.text, lineno=element.sourceline)

    def _get_element_text(self, tree, name):
        element = tree.find(name.text)
        if element is None:
            raise MissingElement(
                '<atom:{}>'.format(name.localname),
                lineno=tree.sourceline
            )
        return element.text
