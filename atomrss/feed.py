"""
    atomrss.feed
    ~~~~~~~~~~~~

    An abstraction over the :mod:`atomrss.atom` and :mod:`atomrss.rss` modules,
    providing a common interface for parsing and extracting information from
    any kind of feed.

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from abc import ABCMeta, abstractmethod

import lxml.etree

from atomrss import atom, rss
from atomrss.exceptions import AtomRSSError


class NotAFeed(AtomRSSError):
    pass


def parse(source):
    tree = lxml.etree.parse(source)
    return parse_tree(tree)


def parse_tree(tree):
    try:
        return AtomFeed(atom.parse_tree(tree))
    except atom.InvalidRoot:
        try:
            return RSSFeed(rss.parse_tree(tree))
        except rss.InvalidRoot:
            raise NotAFeed(tree.docinfo.URL or tree)


class Feed(metaclass=ABCMeta):
    @property
    @abstractmethod
    def title(self):
        """
        The title of the feed as :class:`Text` instance.
        """

    @property
    @abstractmethod
    def links(self):
        """
        A list of :class:`Link` instances.
        """

    @property
    def website(self):
        """
        An optional :class:`Link` instance to a website corresponding to this
        entry.
        """
        return _get_alternate_link(self.links)

    @property
    @abstractmethod
    def entries(self):
        """
        A list of :class:`Entry` instances.
        """


class Entry(metaclass=ABCMeta):
    @property
    @abstractmethod
    def title(self):
        """
        An optional title as a :class:`Text` instance.
        """

    @property
    @abstractmethod
    def links(self):
        """
        A list of :class:`Link` instances.
        """

    @property
    def website(self):
        """
        An optional :class:`Link` instance to a website corresponding to this
        entry.
        """
        return _get_alternate_link(self.links)

    @property
    @abstractmethod
    def content(self):
        """
        An optional :class:`Content` instance. This may be represent the entire
        content, a link to the content or merely a summary of the content.
        """


class Text:
    def __init__(self, format, value):
        #: The text format either `text` or `html`.
        self.format = format

        #: The actual string.
        self.value = value


class Content:
    def __init__(self, format='html', value=None, source=None):
        #: The format of the content, `text`, `html`, or, if `source` is
        #: present, a mime type.
        self.format = format

        #: An optional string representing the actual content. This string will
        #: be present iff :attr:`source` is not.
        self.value = value

        #: An optional URL to a website with the actual content. This URL will
        #: be present iff :attr:`value` is not.
        self.source = source


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


def _get_alternate_link(links):
    alternates = [
        link for link in links
        if link.rel == 'alternate' and link.type == 'text/html'
    ]
    if alternates:
        for link in alternates:
            if link.hreflang is None:
                # Pick original, if translations are present.
                return link

        return alternates[0]


class AtomFeed(Feed):
    def __init__(self, feed):
        self.feed = feed

    @property
    def title(self):
        return Text(self.feed.title.type, self.feed.title.value)

    @property
    def links(self):
        return [
            Link(
                link.href, rel=link.rel, type=link.type,
                hreflang=link.hreflang,
                title=link.title, length=link.length
            ) for link in self.feed.links
        ]

    @property
    def entries(self):
        return [AtomEntry(entry) for entry in self.feed.entries]


class AtomEntry(Entry):
    def __init__(self, entry):
        self.entry = entry

    @property
    def title(self):
        return Text(self.entry.title.type, self.entry.title.value)

    @property
    def links(self):
        return [
            Link(
                link.href, rel=link.rel, type=link.type,
                hreflang=link.hreflang,
                title=link.title, length=link.length
            ) for link in self.entry.links
        ]

    @property
    def content(self):
        if self.entry.content is not None:
            return Content(
                format=self.entry.content.type,
                source=self.entry.content.src,
                value=self.entry.content.value
            )
        elif self.entry.summary is not None:
            return Content(
                format=self.entry.summary.type,
                value=self.entry.summary.value
            )


class RSSFeed(Feed):
    def __init__(self, feed):
        self.feed = feed

    @property
    def title(self):
        return Text('text', self.feed.channel.title)

    @property
    def links(self):
        return [
            Link(self.feed.channel.link, rel='alternate', type='text/html')
        ]

    @property
    def entries(self):
        return [RSSEntry(entry) for entry in self.feed.entries]


class RSSEntry(Entry):
    def __init__(self, item):
        self.item = item

    @property
    def title(self):
        if self.item.title is not None:
            return Text('text', self.item.title)

    @property
    def links(self):
        links = []
        if self.item.link is not None:
            links.append(
                Link(self.item.link, rel='alternate', type='text/html')
            )
        if self.item.enclosure is not None:
            links.append(
                Link(
                    self.item.enclosure.url,
                    rel='enclosure',
                    type=self.item.enclosure.type,
                    length=self.item.enclosure.length
                )
            )
        return links

    @property
    def content(self):
        return Content(format='html', value=self.item.description)
