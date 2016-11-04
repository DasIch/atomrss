"""
    tests.test_feed
    ~~~~~~~~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import atomrss.feed


def test_atom_examples_parseable(atom_example_path):
    atomrss.feed.parse(atom_example_path)


def test_rss_examples_parseable(rss_example_path):
    atomrss.rss.parse(rss_example_path)


def test_popular_feed_parseable(popular_feed_example):
    atomrss.feed.parse(popular_feed_example)
