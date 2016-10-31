"""
    tests.test_rss
    ~~~~~~~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import os
import csv
from io import BytesIO

import lxml
import requests
import pytest

import atomrss.rss


TESTS_DIR = os.path.dirname(__file__)
PROJECT_DIR = os.path.dirname(TESTS_DIR)
EXAMPLES_DIR = os.path.join(PROJECT_DIR, 'examples')
RSS_EXAMPLES_DIR = os.path.join(EXAMPLES_DIR, 'rss')


@pytest.fixture(params=os.listdir(RSS_EXAMPLES_DIR))
def rss_example_path(request):
    return os.path.join(RSS_EXAMPLES_DIR, request.param)


def _popular_examples():
    with open(os.path.join(EXAMPLES_DIR, 'popular.csv'), 'r') as f:
        return [row[1] for row in csv.reader(f, delimiter='\t')]


@pytest.fixture(params=_popular_examples())
def popular_feed_example_url(request):
    return request.param


@pytest.fixture
def popular_feed_example(request, popular_feed_example_url):
    cache_key = 'feeds/{}'.format(popular_feed_example_url)
    feed = request.config.cache.get(cache_key, None)
    if feed is None:
        response = requests.get(popular_feed_example_url)
        assert response.ok
        feed = response.content
        response.close()
        request.config.cache.set(cache_key, feed.decode('latin1'))
    else:
        feed = feed.encode('latin1')
    return BytesIO(feed)


def test_rss_examples_parseable(rss_example_path):
    atomrss.rss.parse(rss_example_path)


def parser_with_custom_resolver():
    parser = lxml.etree.XMLParser()
    parser.resolvers.add(CustomResolver())
    return parser


def test_popular_feed_parseable(popular_feed_example):
    try:
        atomrss.rss.parse(popular_feed_example)
    except atomrss.rss.InvalidRoot as err:
        pytest.skip(err)
