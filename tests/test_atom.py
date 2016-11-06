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
def feed_title():
    return 'Atom Test Feed'


@pytest.fixture
def feed_updated():
    return datetime.datetime.utcnow().isoformat()


@pytest.fixture
def simple_feed_tree(feed_id, feed_title, feed_updated):
    """
    The simplest possible valid Atom feed as an lxml element tree.
    """
    return ATOME.feed(
        ATOME('id', feed_id),
        ATOME('title', feed_title),
        ATOME('updated', feed_updated)
    ).getroottree()


@pytest.fixture
def entry_id():
    return uuid.uuid4().urn


@pytest.fixture
def entry_title():
    return 'Atom Test Entry'


@pytest.fixture
def entry_updated():
    return datetime.datetime.utcnow().isoformat()


@pytest.fixture
def simple_entry_tree(entry_id, entry_title, entry_updated):
    """
    The simplest possible valid Atom entry as an lxml element tree.
    """
    return ATOME.entry(
        ATOME('id', entry_id),
        ATOME('title', entry_title),
        ATOME('updated', entry_updated)
    ).getroottree()


def test_atom_examples_parseable(atom_example_path):
    atomrss.atom.parse(atom_example_path)


def test_popular_feed_parseable(popular_feed_example):
    try:
        atomrss.atom.parse(popular_feed_example)
    except atomrss.atom.InvalidRoot as err:
        pytest.skip('requires an Atom feed: {}'.format(err))


class FeedAttributeTestCase:
    # Alias
    @pytest.fixture
    def tree(self, simple_feed_tree):
        return simple_feed_tree

    @pytest.fixture
    def element(self, tree):
        return tree.getroot()


class FeedRequiredAttributeTestCase(FeedAttributeTestCase):
    element_name = None

    def test_missing(self, element, tree):
        name = lxml.etree.QName(atomrss.atom.ATOM_NAMESPACE, self.element_name)
        element.remove(element.find(name))

        with pytest.raises(atomrss.atom.MissingElement) as exc:
            atomrss.atom.parse_tree(tree)

        exc.match('<atom:{}>'.format(self.element_name))


class TestFeedAttributeID(FeedRequiredAttributeTestCase):
    element_name = 'id'

    def test(self, feed_id, tree):
        feed = atomrss.atom.parse_tree(tree)
        assert feed.id == feed_id


class TestFeedAttributeTitle(FeedRequiredAttributeTestCase):
    element_name = 'title'

    def test_text(self, feed_title, tree):
        feed = atomrss.atom.parse_tree(tree)
        assert feed.title.type == 'text'
        assert feed.title.value == feed_title


class TestFeedAttributeUpdated(FeedRequiredAttributeTestCase):
    element_name = 'updated'

    def test(self, feed_updated, tree):
        feed = atomrss.atom.parse_tree(tree)
        assert feed.updated.isoformat() == feed_updated


class TestFeedAttributeSubtitle(FeedAttributeTestCase):
    def test_missing(self, tree):
        feed = atomrss.atom.parse_tree(tree)
        assert feed.subtitle is None

    def test_text(self, element, tree):
        element.append(
            ATOME('subtitle', 'Atom Test Feed Subtitle')
        )

        feed = atomrss.atom.parse_tree(tree)
        assert feed.subtitle.type == 'text'
        assert feed.subtitle.value == 'Atom Test Feed Subtitle'


class TestFeedAttributeLinks(FeedAttributeTestCase):
    def test_missing(self, tree):
        feed = atomrss.atom.parse_tree(tree)
        assert feed.links == []

    def test_alternate(self, element, tree):
        element.append(
            ATOME.link(href='http://example.com')
        )

        feed = atomrss.atom.parse_tree(tree)
        assert feed.links == [
            atomrss.atom.Link(
                'http://example.com',
                rel='alternate'
            )
        ]


class TestFeedAttributeAuthors(FeedAttributeTestCase):
    def test_missing(self, tree):
        feed = atomrss.atom.parse_tree(tree)
        assert feed.authors == []

    def test_name(self, element, tree):
        element.append(
            ATOME.author(
                ATOME('name', 'Test Feed Author')
            )
        )

        feed = atomrss.atom.parse_tree(tree)
        assert feed.authors == [
            atomrss.atom.Person('Test Feed Author', None, None)
        ]


class TestFeedAttributeContributors(FeedAttributeTestCase):

    def test_missing(self, tree):
        feed = atomrss.atom.parse_tree(tree)
        assert feed.contributors == []

    def test_name(self, element, tree):
        element.append(
            ATOME.contributor(
                ATOME('name', 'Test Feed Contributor')
            )
        )

        feed = atomrss.atom.parse_tree(tree)
        assert feed.contributors == [
            atomrss.atom.Person('Test Feed Contributor', None, None)
        ]


class EntryAttributeTestCase:
    @pytest.fixture
    def tree(self, simple_feed_tree, simple_entry_tree):
        feed_element = simple_feed_tree.getroot()
        entry_element = simple_entry_tree.getroot()
        feed_element.append(entry_element)
        return simple_feed_tree

    @pytest.fixture
    def element(self, simple_entry_tree):
        return simple_entry_tree.getroot()

    def parse(self, tree):
        feed = atomrss.atom.parse_tree(tree)
        return feed.entries[0]


class TestEntryAttributeID(EntryAttributeTestCase):
    def test(self, entry_id, tree):
        entry = self.parse(tree)
        assert entry.id == entry_id


class TestEntryAttributeTitle(EntryAttributeTestCase):
    def test(self, entry_title, tree):
        entry = self.parse(tree)
        assert entry.title.type == 'text'
        assert entry.title.value == entry_title


class TestEntryAttributeUpdated(EntryAttributeTestCase):
    def test(self, entry_updated, tree):
        entry = self.parse(tree)
        assert entry.updated.isoformat() == entry_updated


class TestEntryAttributeAuthors(EntryAttributeTestCase):
    def test_missing(self, tree):
        entry = self.parse(tree)
        assert entry.authors == []

    def test_name(self, element, tree):
        element.append(
            ATOME.author(
                ATOME('name', 'Test Entry Author')
            )
        )

        entry = self.parse(tree)
        assert entry.authors == [
            atomrss.atom.Person('Test Entry Author', None, None)
        ]


class TestEntryAttributeContributors(EntryAttributeTestCase):
    def test_missing(self, tree):
        entry = self.parse(tree)
        assert entry.contributors == []

    def test_name(self, element, tree):
        element.append(

            ATOME.contributor(
                ATOME('name', 'Test Entry Contributor')
            )
        )

        entry = self.parse(tree)
        assert entry.contributors == [
            atomrss.atom.Person('Test Entry Contributor', None, None)
        ]


class TestEntryAttributePublished(EntryAttributeTestCase):
    def test_missing(self, tree):
        entry = self.parse(tree)
        assert entry.published is None

    def test(self, element, tree):
        published = datetime.datetime.utcnow().isoformat()
        element.append(
            ATOME('published', published)
        )

        entry = self.parse(tree)
        assert entry.published.isoformat() == published


class TestEntryAttributeSummary(EntryAttributeTestCase):
    def test_missing(self, tree):
        entry = self.parse(tree)
        assert entry.summary is None

    def test_text(self, element, tree):
        element.append(
            ATOME('summary', 'A summary of the entry.')
        )

        entry = self.parse(tree)
        assert entry.summary.type == 'text'
        assert entry.summary.value == 'A summary of the entry.'


class TestEntryAttributeLinks(EntryAttributeTestCase):
    def test_missing(self, tree):
        entry = self.parse(tree)
        assert entry.links == []

    def test_alternate(self, element, tree):
        element.append(
            ATOME.link(href='http://example.com')
        )

        entry = self.parse(tree)
        assert entry.links == [
            atomrss.atom.Link('http://example.com', rel='alternate')
        ]


class TestEntryAttributeContent(EntryAttributeTestCase):
    def test_missing(self, tree):
        entry = self.parse(tree)
        assert entry.content is None

    def test_text(self, element, tree):
        element.append(
            ATOME('content', 'The content of the entry.')
        )

        entry = self.parse(tree)
        assert entry.content.type == 'text'
        assert entry.content.value == 'The content of the entry.'
