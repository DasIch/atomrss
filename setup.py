"""
    setup
    ~~~~~

    :copyright: 2016 by Daniel Neuhäuser
    :license: BSD, see LICENSE.rst for details
"""
from setuptools import setup


setup(
    name='atomrss',
    version='0.1',
    description='Atom and RSS parser',
    url='https://github.com/DasIch/atomrss',
    author='Daniel Neuhäuser',
    author_email='ich@danielneuhaeuser.de',
    packages=['atomrss'],
    install_requires=['lxml', 'structlog', 'python-dateutil']
)
