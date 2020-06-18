#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from pkg_resources import parse_version
from setuptools import setup, __version__ as setuptools_version


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('NEWS') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

test_requirements = [
]

def has_environment_marker_platform_impl_support():
    """Code extracted from 'pytest/setup.py'
    https://github.com/pytest-dev/pytest/blob/7538680c/setup.py#L31
    The first known release to support environment marker with range operators
    it is 18.5, see:
    https://setuptools.readthedocs.io/en/latest/history.html#id235
    """
    return parse_version(setuptools_version) >= parse_version('18.5')

install_requires = [
    'w3lib>=1.19.0',
    'lxml',
    'six>=1.6.0',
    'cssselect>=0.9'
]
extras_require = {}

if not has_environment_marker_platform_impl_support():
    if sys.version_info[0:2] < (3, 0):
        install_requires.append("functools32")
else:
    extras_require[":python_version<'3.0'"] = ["functools32"]

setup(
    name='parsel',
    version='1.6.0',
    description="Parsel is a library to extract data from HTML and XML using XPath and CSS selectors",
    long_description=readme + '\n\n' + history,
    author="Scrapy project",
    author_email='info@scrapy.org',
    url='https://github.com/scrapy/parsel',
    packages=[
        'parsel',
    ],
    package_dir={'parsel':
                 'parsel'},
    include_package_data=True,
    install_requires=install_requires,
    extras_require=extras_require,
    license="BSD",
    zip_safe=False,
    keywords='parsel',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Topic :: Text Processing :: Markup',
        'Topic :: Text Processing :: Markup :: HTML',
        'Topic :: Text Processing :: Markup :: XML',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    setup_requires=['pytest-runner',],
    tests_require=['pytest',],
    test_suite='tests',
)
