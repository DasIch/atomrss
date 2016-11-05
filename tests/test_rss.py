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


class TestChannel:
    def test_feed_title(self, feed_title, simple_feed_tree):
        feed = atomrss.rss.parse_tree(simple_feed_tree)
        assert feed.channel.title == feed_title

    def test_feed_link(self, feed_link, simple_feed_tree):
        feed = atomrss.rss.parse_tree(simple_feed_tree)
        assert feed.channel.link == feed_link

    def test_feed_description(self, feed_description, simple_feed_tree):
        feed = atomrss.rss.parse_tree(simple_feed_tree)
        assert feed.channel.description == feed_description


class TestItem:
    @pytest.fixture
    def feed_tree(self, simple_item_tree, simple_feed_tree):
        channel = simple_feed_tree.find('channel')
        channel.append(simple_item_tree.getroot())
        return simple_feed_tree

    def test_title(self, item_title, feed_tree):
        feed = atomrss.rss.parse_tree(feed_tree)
        item = feed.channel.items[0]
        assert item.title == item_title

    def test_link(self, item_link, feed_tree):
        feed = atomrss.rss.parse_tree(feed_tree)
        item = feed.channel.items[0]
        assert item.link == item_link

    def test_description_without_item_description(self, feed_tree):
        feed = atomrss.rss.parse_tree(feed_tree)
        item = feed.channel.items[0]
        assert item.description is None

    def test_description(self, feed_tree):
        feed_tree.find('channel/item').append(
            E('description', 'Item description')
        )

        feed = atomrss.rss.parse_tree(feed_tree)
        item = feed.channel.items[0]
        assert item.description == 'Item description'

    def test_author_without_item_author(self, feed_tree):
        feed = atomrss.rss.parse_tree(feed_tree)
        item = feed.channel.items[0]
        assert item.author is None

    def test_author(self, feed_tree):
        feed_tree.find('channel/item').append(
            E('author', 'author@example.com (Item Author)')
        )

        feed = atomrss.rss.parse_tree(feed_tree)
        item = feed.channel.items[0]
        assert item.author.name == 'Item Author'
        assert item.author.email == 'author@example.com'
