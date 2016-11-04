"""
    tests.test_atom
    ~~~~~~~~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import uuid
import datetime

import pytest
import lxml.etree
import lxml.builder

import atomrss.atom


ATOME = lxml.builder.ElementMaker(namespace=atomrss.atom.ATOM_NAMESPACE)


@pytest.fixture
def feed_id():
    return uuid.uuid4().urn


@pytest.fixture
def feed_updated():
    return datetime.datetime.utcnow().isoformat()


@pytest.fixture
def simple_feed_tree(feed_id, feed_updated):
    """
    The simplest possible valid Atom feed as an lxml element tree.
    """
    return ATOME.feed(
        ATOME('id', feed_id),
        ATOME('title', 'Atom Test Feed'),
        ATOME('updated', feed_updated)
    ).getroottree()


@pytest.fixture
def entry_id():
    return uuid.uuid4().urn


@pytest.fixture
def entry_updated():
    return datetime.datetime.utcnow().isoformat()


@pytest.fixture
def simple_entry_tree(entry_id, entry_updated):
    """
    The simplest possible valid Atom entry as an lxml element tree.
    """
    return ATOME.entry(
        ATOME('id', entry_id),
        ATOME('title', 'Atom Test Entry'),
        ATOME('updated', entry_updated)
    ).getroottree()


def test_atom_examples_parseable(atom_example_path):
    atomrss.atom.parse(atom_example_path)


def test_popular_feed_parseable(popular_feed_example):
    try:
        atomrss.atom.parse(popular_feed_example)
    except atomrss.atom.InvalidRoot as err:
        pytest.skip('requires an Atom feed: {}'.format(err))


class TestFeed:
    def test_id(self, feed_id, simple_feed_tree):
        feed = atomrss.atom.parse_tree(simple_feed_tree)
        assert feed.id == feed_id

    def test_title(self, simple_feed_tree):
        feed = atomrss.atom.parse_tree(simple_feed_tree)
        assert feed.title.type == 'text'
        assert feed.title.value == 'Atom Test Feed'

    def test_updated(self, feed_updated, simple_feed_tree):
        feed = atomrss.atom.parse_tree(simple_feed_tree)
        assert feed.updated.isoformat() == feed_updated

    def test_subtitle_on_feed_without_subtitle(self, simple_feed_tree):
        feed = atomrss.atom.parse_tree(simple_feed_tree)
        assert feed.subtitle is None

    def test_subtitle_on_feed_with_subtitle(self, simple_feed_tree):
        feed_element = simple_feed_tree.getroot()
        feed_element.append(
            ATOME('subtitle', 'Atom Test Feed Subtitle')
        )

        feed = atomrss.atom.parse_tree(simple_feed_tree)
        assert feed.subtitle.type == 'text'
        assert feed.subtitle.value == 'Atom Test Feed Subtitle'

    def test_links_on_feed_without_links(self, simple_feed_tree):
        feed = atomrss.atom.parse_tree(simple_feed_tree)
        assert feed.links == []

    def test_links(self, simple_feed_tree):
        element = simple_feed_tree.getroot()
        element.append(
            ATOME.link(href='http://example.com')
        )
        feed = atomrss.atom.parse_tree(simple_feed_tree)
        assert feed.links == [
            atomrss.atom.Link(
                'http://example.com',
                rel='alternate'
            )
        ]

    def test_authors_on_feed_without_authors(self, simple_feed_tree):
        feed = atomrss.atom.parse_tree(simple_feed_tree)
        assert feed.authors == []


    def test_authors(self, simple_feed_tree):
        element = simple_feed_tree.getroot()
        element.append(
            ATOME.author(
                ATOME('name', 'Test Feed Author')
            )
        )

        feed = atomrss.atom.parse_tree(simple_feed_tree)
        assert feed.authors == [
            atomrss.atom.Person('Test Feed Author', None, None)
        ]

    def test_contributors_on_feed_without_contributors(self, simple_feed_tree):
        feed = atomrss.atom.parse_tree(simple_feed_tree)
        assert feed.contributors == []

    def test_contributors(self, simple_feed_tree):
        element = simple_feed_tree.getroot()
        element.append(
            ATOME.contributor(
                ATOME('name', 'Test Feed Contributor')
            )
        )

        feed = atomrss.atom.parse_tree(simple_feed_tree)
        assert feed.contributors == [
            atomrss.atom.Person('Test Feed Contributor', None, None)
        ]


class TestEntry:
    @pytest.fixture
    def feed_tree(self, simple_feed_tree, simple_entry_tree):
        simple_feed_tree.getroot().append(simple_entry_tree.getroot())
        return simple_feed_tree

    def test_id(self, entry_id, feed_tree):
        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.id == entry_id

    def test_title(self, feed_tree):
        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.title.type == 'text'
        assert entry.title.value == 'Atom Test Entry'

    def test_updated(self, entry_updated, feed_tree):
        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.updated.isoformat() == entry_updated

    def test_authors_on_entry_without_authors(self, feed_tree):
        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.authors == []

    def test_authors(self, simple_entry_tree, feed_tree):
        element = simple_entry_tree.getroot()
        element.append(
            ATOME.author(
                ATOME('name', 'Test Entry Author')
            )
        )

        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.authors == [
            atomrss.atom.Person('Test Entry Author', None, None)
        ]

    def test_contributors_on_entry_without_contributors(self, feed_tree):
        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.contributors == []

    def test_contributors(self, simple_entry_tree, feed_tree):
        element = simple_entry_tree.getroot()
        element.append(
            ATOME.contributor(
                ATOME('name', 'Test Entry Contributor')
            )
        )

        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.contributors == [
            atomrss.atom.Person('Test Entry Contributor', None, None)
        ]

    def test_published_on_entry_without_published(self, feed_tree):
        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.published is None

    def test_published(self, simple_entry_tree, feed_tree):
        element = simple_entry_tree.getroot()
        published = datetime.datetime.utcnow().isoformat()
        element.append(
            ATOME('published', published)
        )

        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.published.isoformat() == published

    def test_summary_on_entry_without_summary(self, feed_tree):
        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.summary is None

    def test_summary(self, simple_entry_tree, feed_tree):
        element = simple_entry_tree.getroot()
        element.append(
            ATOME('summary', 'A summary of the entry.')
        )

        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.summary.type == 'text'
        assert entry.summary.value == 'A summary of the entry.'

    def test_links_on_entry_without_links(self, feed_tree):
        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.links == []

    def test_links(self, simple_entry_tree, feed_tree):
        element = simple_entry_tree.getroot()
        element.append(
            ATOME.link(href='http://example.com')
        )

        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.links == [
            atomrss.atom.Link('http://example.com', rel='alternate')
        ]

    def test_content_on_entry_without_content(self, feed_tree):
        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.content is None

    def test_content(self, simple_entry_tree, feed_tree):
        element = simple_entry_tree.getroot()
        element.append(
            ATOME('content', 'The content of the entry.')
        )

        feed = atomrss.atom.parse_tree(feed_tree)
        entry = feed.entries[0]
        assert entry.content.type == 'text'
        assert entry.content.value == 'The content of the entry.'
