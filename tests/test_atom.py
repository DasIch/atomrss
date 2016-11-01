"""
    tests.test_atom
    ~~~~~~~~~~~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
import pytest

import atomrss.atom


def test_atom_examples_parseable(atom_example_path):
    atomrss.atom.parse(atom_example_path)


def test_popular_feed_parseable(popular_feed_example):
    try:
        atomrss.atom.parse(popular_feed_example)
    except atomrss.atom.InvalidRoot as err:
        pytest.skip('requires an Atom feed: {}'.format(err))
