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
def atom_feed_id():
    return uuid.uuid4().urn


@pytest.fixture
def atom_feed_updated():
    return datetime.datetime.utcnow().isoformat()


@pytest.fixture
def simple_atom_feed(atom_feed_id, atom_feed_updated):
    """
    The simplest possible valid Atom feed as an lxml element tree.
    """
    return ATOME.feed(
        ATOME('id', atom_feed_id),
        ATOME('title', 'Atom Test Feed'),
        ATOME('updated', atom_feed_updated)
    ).getroottree()


@pytest.fixture
def atom_entry_id():
    return uuid.uuid4().urn


@pytest.fixture
def atom_entry_updated():
    return datetime.datetime.utcnow().isoformat()


@pytest.fixture
def simple_atom_entry(atom_entry_id, atom_entry_updated):
    """
    The simplest possible valid Atom entry as an lxml element tree.
    """
    return ATOME.entry(
        ATOME('id', atom_entry_id),
        ATOME('title', 'Atom Test Entry'),
        ATOME('updated', atom_entry_updated)
    ).getroottree()


def test_atom_examples_parseable(atom_example_path):
    atomrss.atom.parse(atom_example_path)


def test_popular_feed_parseable(popular_feed_example):
    try:
        atomrss.atom.parse(popular_feed_example)
    except atomrss.atom.InvalidRoot as err:
        pytest.skip('requires an Atom feed: {}'.format(err))


class TestFeed:
    def test_id(self, atom_feed_id, simple_atom_feed):
        feed = atomrss.atom.parse_tree(simple_atom_feed)
        assert feed.id == atom_feed_id

    def test_title(self, simple_atom_feed):
        feed = atomrss.atom.parse_tree(simple_atom_feed)
        assert feed.title.type == 'text'
        assert feed.title.value == 'Atom Test Feed'

    def test_updated(self, atom_feed_updated, simple_atom_feed):
        feed = atomrss.atom.parse_tree(simple_atom_feed)
        assert feed.updated.isoformat() == atom_feed_updated

    def test_subtitle_on_feed_without_subtitle(self, simple_atom_feed):
        feed = atomrss.atom.parse_tree(simple_atom_feed)
        assert feed.subtitle is None

    def test_subtitle_on_feed_with_subtitle(self, simple_atom_feed):
        feed_element = simple_atom_feed.getroot()
        feed_element.append(
            ATOME('subtitle', 'Atom Test Feed Subtitle')
        )

        feed = atomrss.atom.parse_tree(simple_atom_feed)
        assert feed.subtitle.type == 'text'
        assert feed.subtitle.value == 'Atom Test Feed Subtitle'

    def test_links_on_feed_without_links(self, simple_atom_feed):
        feed = atomrss.atom.parse_tree(simple_atom_feed)
        assert feed.links == []

    def test_links(self, simple_atom_feed):
        element = simple_atom_feed.getroot()
        element.append(
            ATOME.link(href='http://example.com')
        )
        feed = atomrss.atom.parse_tree(simple_atom_feed)
        assert feed.links == [
            atomrss.atom.Link(
                'http://example.com',
                rel='alternate'
            )
        ]

    def test_authors_on_feed_without_authors(self, simple_atom_feed):
        feed = atomrss.atom.parse_tree(simple_atom_feed)
        assert feed.authors == []


    def test_authors(self, simple_atom_feed):
        element = simple_atom_feed.getroot()
        element.append(
            ATOME.author(
                ATOME('name', 'Test Feed Author')
            )
        )

        feed = atomrss.atom.parse_tree(simple_atom_feed)
        assert feed.authors == [
            atomrss.atom.Person('Test Feed Author', None, None)
        ]

    def test_contributors_on_feed_without_contributors(self, simple_atom_feed):
        feed = atomrss.atom.parse_tree(simple_atom_feed)
        assert feed.contributors == []

    def test_contributors(self, simple_atom_feed):
        element = simple_atom_feed.getroot()
        element.append(
            ATOME.contributor(
                ATOME('name', 'Test Feed Contributor')
            )
        )

        feed = atomrss.atom.parse_tree(simple_atom_feed)
        assert feed.contributors == [
            atomrss.atom.Person('Test Feed Contributor', None, None)
        ]


class TestEntry:
    @pytest.fixture
    def atom_feed(self, simple_atom_feed, simple_atom_entry):
        simple_atom_feed.getroot().append(simple_atom_entry.getroot())
        return simple_atom_feed

    def test_id(self, atom_entry_id, atom_feed):
        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.id == atom_entry_id

    def test_title(self, atom_entry_id, atom_feed):
        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.title.type == 'text'
        assert entry.title.value == 'Atom Test Entry'

    def test_updated(self, atom_entry_updated, atom_feed):
        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.updated.isoformat() == atom_entry_updated

    def test_authors_on_entry_without_authors(self, atom_feed):
        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.authors == []

    def test_authors(self, simple_atom_entry, atom_feed):
        element = simple_atom_entry.getroot()
        element.append(
            ATOME.author(
                ATOME('name', 'Test Entry Author')
            )
        )

        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.authors == [
            atomrss.atom.Person('Test Entry Author', None, None)
        ]

    def test_contributors_on_entry_without_contributors(self, atom_feed):
        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.contributors == []

    def test_contributors(self, simple_atom_entry, atom_feed):
        element = simple_atom_entry.getroot()
        element.append(
            ATOME.contributor(
                ATOME('name', 'Test Entry Contributor')
            )
        )

        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.contributors == [
            atomrss.atom.Person('Test Entry Contributor', None, None)
        ]

    def test_published_on_entry_without_published(self, atom_feed):
        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.published is None

    def test_published(self, simple_atom_entry, atom_feed):
        element = simple_atom_entry.getroot()
        published = datetime.datetime.utcnow().isoformat()
        element.append(
            ATOME('published', published)
        )

        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.published.isoformat() == published

    def test_summary_on_entry_without_summary(self, atom_feed):
        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.summary is None

    def test_summary(self, simple_atom_entry, atom_feed):
        element = simple_atom_entry.getroot()
        element.append(
            ATOME('summary', 'A summary of the entry.')
        )

        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.summary.type == 'text'
        assert entry.summary.value == 'A summary of the entry.'

    def test_links_on_entry_without_links(self, atom_feed):
        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.links == []

    def test_links(self, simple_atom_entry, atom_feed):
        element = simple_atom_entry.getroot()
        element.append(
            ATOME.link(href='http://example.com')
        )

        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.links == [
            atomrss.atom.Link('http://example.com', rel='alternate')
        ]

    def test_content_on_entry_without_content(self, atom_feed):
        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.content is None

    def test_content(self, simple_atom_entry, atom_feed):
        element = simple_atom_entry.getroot()
        element.append(
            ATOME('content', 'The content of the entry.')
        )

        feed = atomrss.atom.parse_tree(atom_feed)
        entry = feed.entries[0]
        assert entry.content.type == 'text'
        assert entry.content.value == 'The content of the entry.'
