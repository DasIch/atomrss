"""
    tests.test_rss
    ~~~~~~~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import pytest
from lxml.builder import E

import atomrss.rss


@pytest.fixture
def feed_title():
    return 'RSS Feed Title'


@pytest.fixture
def feed_link():
    return 'http://example.com/feed'


@pytest.fixture
def feed_description():
    return 'RSS Feed Description'


@pytest.fixture
def simple_feed_tree(feed_title, feed_link, feed_description):
    return E.rss(
        E.channel(
            E('title', feed_title),
            E('link', feed_link),
            E('description', feed_description)
        ),
        version='2.0'
    ).getroottree()


@pytest.fixture
def item_title():
    return 'RSS Entry Title'


@pytest.fixture
def item_link():
    return 'http://example.com/entry'


@pytest.fixture
def simple_item_tree(item_title, item_link):
    return E.item(
        E('title', item_title),
        E('link', item_link)
    ).getroottree()


def test_rss_examples_parseable(rss_example_path):
    atomrss.rss.parse(rss_example_path)


def test_popular_feed_parseable(popular_feed_example):
    try:
        atomrss.rss.parse(popular_feed_example)
    except atomrss.rss.InvalidRoot as err:
        pytest.skip('requires an RSS feed: {}'.format(err))


class ChannelAttributeTestCase:
    # Alias
    @pytest.fixture
    def tree(self, simple_feed_tree):
        return simple_feed_tree

    @pytest.fixture
    def element(self, simple_feed_tree):
        return simple_feed_tree.find('channel')


class ChannelRequiredAttributeTestCase(ChannelAttributeTestCase):
    element_name = None

    def test_missing(self, element, tree):
        element.remove(tree.find('channel/{}'.format(self.element_name)))

        with pytest.raises(atomrss.rss.MissingElement) as exc:
            atomrss.rss.parse_tree(tree)

        exc.match('<{}>'.format(self.element_name))


class TestChannelAttributeTitle(ChannelRequiredAttributeTestCase):
    element_name = 'title'

    def test(self, feed_title, tree):
        feed = atomrss.rss.parse_tree(tree)
        assert feed.channel.title == feed_title


class TestChannelAttributeLink(ChannelRequiredAttributeTestCase):
    element_name = 'link'

    def test(self, feed_link, tree):
        feed = atomrss.rss.parse_tree(tree)
        assert feed.channel.link == feed_link


class TestChannelAttributeDescription(ChannelRequiredAttributeTestCase):
    element_name = 'description'

    def test(self, feed_description, tree):
        feed = atomrss.rss.parse_tree(tree)
        assert feed.channel.description == feed_description


class ItemAttributeTestCase:
    @pytest.fixture
    def tree(self, simple_feed_tree, simple_item_tree):
        channel = simple_feed_tree.find('channel')
        channel.append(simple_item_tree.getroot())
        return simple_feed_tree

    @pytest.fixture
    def element(self, tree):
        return tree.find('channel/item')

    def parse(self, tree):
        feed = atomrss.rss.parse_tree(tree)
        return feed.channel.items[0]


class TestItemAttributeTitle(ItemAttributeTestCase):
    def test_missing(self, element, tree):
        element.remove(element.find('title'))
        assert element.find('description') is None

        feed = atomrss.rss.parse_tree(tree)
        assert feed.channel.items == []

    def test_replaced_by_description(self, element, tree):
        element.remove(element.find('title'))
        element.append(
            E('description', 'Item description')
        )

        item = self.parse(tree)
        assert item.title is None
        assert item.description == 'Item description'

    def test(self, item_title, tree):
        item = self.parse(tree)
        assert item.title == item_title


class TestItemAttributeLink(ItemAttributeTestCase):
    def test(self, item_link, tree):
        item = self.parse(tree)
        assert item.link == item_link


class TestItemAttributeDescription(ItemAttributeTestCase):
    # test_missing is handled in TestItemAttributeTitle

    def test_replaced_by_title(self, element, tree):
        assert element.find('title') is not None
        item = self.parse(tree)
        assert item.description is None

    def test(self, element, tree):
        element.append(
            E('description', 'Item description')
        )

        item = self.parse(tree)
        assert item.description == 'Item description'


class TestItemAttributeAuthor(ItemAttributeTestCase):
    def test_missing(self, tree):
        item = self.parse(tree)
        assert item.author is None

    def test(self, element, tree):
        element.append(
            E('author', 'author@example.com (Item Author)')
        )

        item = self.parse(tree)
        assert item.author.name == 'Item Author'
        assert item.author.email == 'author@example.com'
