#!/usr/bin/env python

import sys

from pkg_resources import parse_version
from setuptools import setup, __version__ as setuptools_version


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('NEWS') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

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
    package_dir={
        'parsel': 'parsel',
    },
    include_package_data=True,
    install_requires=[
        'w3lib>=1.19.0',
        'lxml',
        'six>=1.6.0',
        'cssselect>=0.9'
    ],
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
