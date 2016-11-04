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
    try:
        return AtomFeed(atom.parse_tree(tree))
    except atom.InvalidRoot:
        try:
            return RSSFeed(rss.parse_tree(tree))
        except rss.InvalidRoot:
            raise NotAFeed(source)


class Feed(metaclass=ABCMeta):
    @property
    @abstractmethod
    def title(self):
        """
        The title of the feed.
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
        An optional title.
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
        self.feed.title

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
        return self.entry.title

    @property
    def links(self):
        return [
            Link(
                link.href, rel=link.rel, type=link.type,
                hreflang=link.hreflang,
                title=link.title, length=link.length
            ) for link in self.feed.links
        ]


class RSSFeed(Feed):
    def __init__(self, feed):
        self.feed = feed

    @property
    def title(self):
        return self.feed.channel.title

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
        return self.item.title

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
