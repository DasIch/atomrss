"""
    tests.test_rss
    ~~~~~~~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import pytest

import atomrss.rss


def test_rss_examples_parseable(rss_example_path):
    atomrss.rss.parse(rss_example_path)


def test_popular_feed_parseable(popular_feed_example):
    try:
        atomrss.rss.parse(popular_feed_example)
    except atomrss.rss.InvalidRoot as err:
        pytest.skip('requires an RSS feed: {}'.format(err))
