"""
    tests.test_feed
    ~~~~~~~~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import datetime
import uuid

import pytest

from atomrss import atom, rss
import atomrss.feed


def test_atom_examples_parseable(atom_example_path):
    atomrss.feed.parse(atom_example_path)


def test_rss_examples_parseable(rss_example_path):
    atomrss.rss.parse(rss_example_path)


def test_popular_feed_parseable(popular_feed_example):
    atomrss.feed.parse(popular_feed_example)


class FeedAttributeTestCase:
    pass


class TestFeedAttributeTitle(FeedAttributeTestCase):
    def test_atom(self):
        atom_feed = atom.Feed(
            id=uuid.uuid4().urn,
            title=atom.Text('text', 'Atom Feed Title'),
            updated=datetime.datetime.utcnow(),
            entries=[]
        )
        feed = atomrss.feed.AtomFeed(atom_feed)
        assert feed.title.format == 'text'
        assert feed.title.value == 'Atom Feed Title'

    def test_rss(self):
        rss_feed = rss.RSS(
            version='2.0',
            channel=rss.Channel(
                title='RSS Feed Title',
                link='http://example.com',
                description='RSS Feed Description',
                items=[]
            )
        )
        feed = atomrss.feed.RSSFeed(rss_feed)
        assert feed.title.format == 'text'
        assert feed.title.value == 'RSS Feed Title'


class TestFeedAttributeLinks(FeedAttributeTestCase):
    def test_atom(self):
        atom_feed = atom.Feed(
            id=uuid.uuid4().urn,
            title=atom.Text('text', 'Atom Feed Title'),
            updated=datetime.datetime.utcnow(),
            entries=[],
            links=[
                atom.Link(
                    href='http://example.com/feed.atom',
                    rel='self',
                    type='application/atom+xml'
                )
            ]
        )
        feed = atomrss.feed.AtomFeed(atom_feed)
        assert feed.links == [
            atomrss.feed.Link(
                href='http://example.com/feed.atom',
                rel='self',
                type='application/atom+xml'
            )
        ]

    def test_rss(self):
        rss_feed = rss.RSS(
            version='2.0',
            channel=rss.Channel(
                title='RSS Feed Title',
                link='http://example.com',
                description='RSS Feed Description',
                items=[]
            )
        )
        feed = atomrss.feed.RSSFeed(rss_feed)
        assert feed.links == [
            atomrss.feed.Link(
                href='http://example.com',
                rel='alternate',
                type='text/html'
            )
        ]


class TestFeedAttributeWebsite(FeedAttributeTestCase):
    def test_atom(self):
        atom_feed = atom.Feed(
            id=uuid.uuid4().urn,
            title=atom.Text('text', 'Atom Feed Title'),
            updated=datetime.datetime.utcnow(),
            entries=[],
            links=[
                atom.Link(
                    href='http://example.com',
                    rel='alternate',
                    type='text/html'
                )
            ]
        )
        feed = atomrss.feed.AtomFeed(atom_feed)
        assert feed.website == atomrss.feed.Link(
            href='http://example.com',
            rel='alternate',
            type='text/html'
        )

    def test_atom_no_alternate(self):
        atom_feed = atom.Feed(
            id=uuid.uuid4().urn,
            title=atom.Text('text', 'Atom Feed Title'),
            updated=datetime.datetime.utcnow(),
            entries=[],
            links=[
                atom.Link(
                    href='http://example.com/feed.atom',
                    rel='self',
                    type='application/atom+xml'
                )
            ]
        )
        feed = atomrss.feed.AtomFeed(atom_feed)
        assert feed.website is None

    def test_atom_translations(self):
        atom_feed = atom.Feed(
            id=uuid.uuid4().urn,
            title=atom.Text('text', 'Atom Feed Title'),
            updated=datetime.datetime.utcnow(),
            entries=[],
            links=[
                atom.Link(
                    href='http://example.com',
                    rel='alternate',
                    type='text/html'
                ),
                atom.Link(
                    href='http://example.com',
                    rel='alternate',
                    type='text/html',
                    hreflang='de-DE'
                )
            ]
        )
        feed = atomrss.feed.AtomFeed(atom_feed)
        assert feed.website == atomrss.feed.Link(
            href='http://example.com',
            rel='alternate',
            type='text/html'
        )

    def test_rss(self):
        rss_feed = rss.RSS(
            version='2.0',
            channel=rss.Channel(
                title='RSS Feed Title',
                link='http://example.com',
                description='RSS Feed Description',
                items=[]
            )
        )
        feed = atomrss.feed.RSSFeed(rss_feed)
        assert feed.website == atomrss.feed.Link(
            href='http://example.com',
            rel='alternate',
            type='text/html'
        )


class EntryAttributeTestCase:
    pass


class TestEntryAttributeTitle(EntryAttributeTestCase):
    def test_atom(self):
        atom_entry = atom.Entry(
            id=uuid.uuid4().urn,
            title=atom.Text('text', 'Atom Entry Title'),
            updated=datetime.datetime.utcnow()
        )
        entry = atomrss.feed.AtomEntry(atom_entry)
        assert entry.title.format == 'text'
        assert entry.title.value == 'Atom Entry Title'

    def test_rss(self):
        rss_item = rss.Item(title='RSS Item Title')
        entry = atomrss.feed.RSSEntry(rss_item)
        assert entry.title.format == 'text'
        assert entry.title.value == 'RSS Item Title'

    def test_rss_without_title(self):
        rss_item = rss.Item(description='RSS Item Description')
        entry = atomrss.feed.RSSEntry(rss_item)
        assert entry.title is None


class TestEntryAttributeLinks(EntryAttributeTestCase):
    def test_atom(self):
        atom_entry = atom.Entry(
            id=uuid.uuid4().urn,
            title=atom.Text('text', 'Atom Entry Title'),
            updated=datetime.datetime.utcnow(),
            links=[
                atom.Link(
                    href='http://example.com',
                    rel='alternate',
                    type='text/html'
                )
            ]
        )
        entry = atomrss.feed.AtomEntry(atom_entry)
        assert entry.links == [
            atomrss.feed.Link(
                href='http://example.com',
                rel='alternate',
                type='text/html'
            )
        ]

    def test_rss(self):
        rss_item = rss.Item(
            title='RSS Item Title',
            link='http://example.com'
        )
        entry = atomrss.feed.RSSEntry(rss_item)
        assert entry.links == [
            atomrss.feed.Link(
                href='http://example.com',
                rel='alternate',
                type='text/html'
            )
        ]


class TestEntryAttributeWebsite(EntryAttributeTestCase):
    def test_atom(self):
        atom_entry = atom.Entry(
            id=uuid.uuid4().urn,
            title=atom.Text('text', 'Atom Entry Title'),
            updated=datetime.datetime.utcnow(),
            links=[
                atom.Link(
                    href='http://example.com',
                    rel='alternate',
                    type='text/html'
                )
            ]
        )
        entry = atomrss.feed.AtomEntry(atom_entry)
        assert entry.website == atomrss.feed.Link(
            href='http://example.com',
            rel='alternate',
            type='text/html'
        )

    def test_rss(self):
        rss_item = rss.Item(
            title='RSS Item Title',
            link='http://example.com'
        )
        entry = atomrss.feed.RSSEntry(rss_item)
        assert entry.website == atomrss.feed.Link(
            href='http://example.com',
            rel='alternate',
            type='text/html'
        )


class TestEntryAttributeContent(EntryAttributeTestCase):
    def test_atom_no_content(self):
        atom_entry = atom.Entry(
            id=uuid.uuid4().urn,
            title=atom.Text('text', 'Atom Entry Title'),
            updated=datetime.datetime.utcnow()
        )
        entry = atomrss.feed.AtomEntry(atom_entry)
        assert entry.content is None

    def test_atom_summary_text(self):
        atom_entry = atom.Entry(
            id=uuid.uuid4().urn,
            title=atom.Text('text', 'Atom Entry Title'),
            updated=datetime.datetime.utcnow(),
            summary=atom.Text('text', 'The summary of the entry.')
        )
        entry = atomrss.feed.AtomEntry(atom_entry)
        assert entry.content.format == 'text'
        assert entry.content.source is None
        assert entry.content.value == 'The summary of the entry.'

    def test_atom_summary_html(self):
        atom_entry = atom.Entry(
            id=uuid.uuid4().urn,
            title=atom.Text('text', 'Atom Entry Title'),
            updated=datetime.datetime.utcnow(),
            summary=atom.Text('html', 'The summary of the entry.')
        )
        entry = atomrss.feed.AtomEntry(atom_entry)
        assert entry.content.format == 'html'
        assert entry.content.source is None
        assert entry.content.value == 'The summary of the entry.'

    def test_atom_content_embedded_text(self):
        atom_entry = atom.Entry(
            id=uuid.uuid4().urn,
            title=atom.Text('text', 'Atom Entry Title'),
            updated=datetime.datetime.utcnow(),
            content=atom.Content(
                'text', None, 'The content of the Atom entry.'
            )
        )
        entry = atomrss.feed.AtomEntry(atom_entry)
        assert entry.content.format == 'text'
        assert entry.content.source is None
        assert entry.content.value == 'The content of the Atom entry.'

    def test_atom_content_embedded_html(self):
        atom_entry = atom.Entry(
            id=uuid.uuid4().urn,
            title=atom.Text('text', 'Atom Entry Title'),
            updated=datetime.datetime.utcnow(),
            content=atom.Content(
                'html', None, 'The content of the Atom entry.'
            )
        )
        entry = atomrss.feed.AtomEntry(atom_entry)
        assert entry.content.format == 'html'
        assert entry.content.source is None
        assert entry.content.value == 'The content of the Atom entry.'

    def test_atom_content_src(self):
        atom_entry = atom.Entry(
            id=uuid.uuid4().urn,
            title=atom.Text('text', 'Atom Entry Title'),
            updated=datetime.datetime.utcnow(),
            content=atom.Content(
                'text/html', 'http://example.com', None
            )
        )
        entry = atomrss.feed.AtomEntry(atom_entry)
        assert entry.content.format == 'text/html'
        assert entry.content.source == 'http://example.com'
        assert entry.content.value is None

    def test_rss(self):
        rss_item = rss.Item(
            title='RSS Item Title',
            description=(
                'The content of this RSS Item.'
            )
        )
        entry = atomrss.feed.RSSEntry(rss_item)
        assert entry.content.format == 'html'
        assert entry.content.source is None
        assert entry.content.value == 'The content of this RSS Item.'
