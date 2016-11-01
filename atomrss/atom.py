"""
    atomrss.atom
    ~~~~~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import logging
from collections import namedtuple

import structlog
import structlog.stdlib
import lxml.etree
import dateutil.parser

from atomrss.exceptions import ParserError


ATOM_NAMESPACE = 'http://www.w3.org/2005/atom'
XHTML_NAMESPACE = 'http://www.w3.org/1999/xhtml'


logger = structlog.wrap_logger(
    logging.getLogger('atomrss.atom'),
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


Text = namedtuple('Text', ['type', 'value'])


Person = namedtuple('Person', ['name', 'uri', 'email'])


Link = namedtuple('Link', ['href', 'rel'])


Content = namedtuple('Content', ['type', 'src', 'value'])


class AtomParserError(ParserError):
    def to_log_kwargs(self):
        return {
            'event': self.args[0],
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
    def __init__(self, date):
        super().__init__(date)
        self.date = date

    def to_log_kwargs(self):
        return {
            'event': 'invalid-date',
            'date': self.date,
            'lineno': self.lineno
        }


def parse(source):
    tree = lxml.etree.parse(source)
    return parse_tree(tree)


def parse_tree(tree):
    return _Parser(tree).parse()


class _Parser:
    def __init__(self, tree):
        self.tree = tree

        self.logger = logger.bind(source=self.tree.docinfo.URL)
        self.namespace = ATOM_NAMESPACE

    def create_name(self, name):
        return lxml.etree.QName(self.namespace, name).text

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

        # TODO: add element support:
        #       * atomCategory*
        #       * atomGenerator?
        #       * atomIcon?
        #       * atomLogo?
        #       * atomRights?
        #       * extensionElement*

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

        # TODO: add element support:
        #       * atomCategory*
        #       * atomRights?
        #       * atomSource?
        #       * extensionElement*

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
            raise MissingElement('<{}>'.format(name), lineno=tree.sourceline)
        return self.parse_text_construct(element)

    def parse_updated(self, tree):
        name = self.create_name('updated')
        element = tree.find(name)
        if element is None:
            raise MissingElement('<{}>'.format(name), lineno=tree.sourceline)

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
        return self.parse_text_construct(element)

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
        rel = element.attrib.get('rel', 'alternate')
        return Link(href, rel)

    def parse_content(self, tree):
        name = self.create_name('content')
        element = tree.find(name)
        if element is None:
            return

        src = element.attrib.get('src')
        type = element.attrib.get('type', 'text')
        if type in {'text', 'html', 'xhtml'}:
            value = self.parse_text_construct(element).value
        return Content(type, src, value)

    def parse_text_construct(self, element):
        type = element.attrib.get('type', 'text')
        if type == 'xhtml':
            divname = lxml.etree.QName(XHTML_NAMESPACE, 'div').text
            value = lxml.etree.tostring(element.find(divname))
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
        element = tree.find(name)
        if element is None:
            raise MissingElement('<{}>'.format(name), lineno=tree.sourceline)
        return element.text