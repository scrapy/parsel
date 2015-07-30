#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

test_requirements = [
]

setup(
    name='parsel',
    version='0.9.0',
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
    install_requires=[
        'w3lib>=1.8.0',
        'lxml',
        'six>=1.5.2',
        'cssselect>=0.9',
    ],
    license="BSD",
    zip_safe=False,
    keywords='parsel',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
)
