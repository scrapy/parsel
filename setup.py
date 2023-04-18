#!/usr/bin/env python

from setuptools import setup


with open("README.rst", encoding="utf-8") as readme_file:
    readme = readme_file.read()

with open("NEWS", encoding="utf-8") as history_file:
    history = history_file.read().replace(".. :changelog:", "")

setup(
    name="parsel",
    version="1.8.1",
    description="Parsel is a library to extract data from HTML and XML using XPath and CSS selectors",
    long_description=readme + "\n\n" + history,
    author="Scrapy project",
    author_email="info@scrapy.org",
    url="https://github.com/scrapy/parsel",
    packages=[
        "parsel",
    ],
    package_dir={
        "parsel": "parsel",
    },
    include_package_data=True,
    install_requires=[
        "cssselect>=0.9",
        "jmespath",
        "lxml",
        "packaging",
        "typing_extensions; python_version < '3.8'",
        "w3lib>=1.19.0",
    ],
    python_requires=">=3.7",
    license="BSD",
    zip_safe=False,
    keywords="parsel",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Topic :: Text Processing :: Markup",
        "Topic :: Text Processing :: Markup :: HTML",
        "Topic :: Text Processing :: Markup :: XML",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    setup_requires=[
        "pytest-runner",
    ],
    tests_require=[
        "pytest",
    ],
    test_suite="tests",
)
