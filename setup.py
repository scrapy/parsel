#!/usr/bin/env python

from setuptools import setup

with open("README.rst", encoding="utf-8") as readme_file:
    readme = readme_file.read()

with open("NEWS", encoding="utf-8") as history_file:
    history = history_file.read().replace(".. :changelog:", "")

setup(
    name="parsel",
    version="1.10.0",
    description="Parsel is a library to extract data from HTML and XML using XPath and CSS selectors",
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/x-rst",
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
        "cssselect>=1.2.0",
        "jmespath",
        "lxml",
        "packaging",
        "w3lib>=1.19.0",
    ],
    python_requires=">=3.9",
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
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
)
