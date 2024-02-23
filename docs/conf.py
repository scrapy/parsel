#!/usr/bin/env python

import os
import sys

# Get the project root dir, which is the parent dir of this
cwd = os.getcwd()
project_root = os.path.dirname(cwd)

# Insert the project root dir as the first element in the PYTHONPATH.
# This lets us ensure that the source package is imported, and that its
# version is used.
sys.path.insert(0, project_root)

import parsel  # noqa: E402

# -- General configuration ---------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "notfound.extension",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "Parsel"
copyright = "2015, Scrapy Project"

# The version info for the project you're documenting, acts as replacement
# for |version| and |release|, also used in various other places throughout
# the built documents.
#
# The short X.Y version.
version = parsel.__version__
# The full version, including alpha/beta/rc tags.
release = parsel.__version__

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

suppress_warnings = ["epub.unknown_project_files"]


# -- Options for HTML output -------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets)
# here, relative to this directory. They are copied after the builtin
# static files, so a file named "default.css" will overwrite the builtin
# "default.css".
html_static_path = ["_static"]

# Output file base name for HTML help builder.
htmlhelp_basename = "parseldoc"


# -- Options for LaTeX output ------------------------------------------

latex_elements = {}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass
# [howto/manual]).
latex_documents = [
    (
        "index",
        "parsel.tex",
        "Parsel Documentation",
        "Scrapy Project",
        "manual",
    ),
]


# -- Options for manual page output ------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ("index", "parsel", "Parsel Documentation", ["Scrapy Project"], 1),
]

# -- Options for Texinfo output ----------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        "index",
        "parsel",
        "Parsel Documentation",
        "Scrapy Project",
        "parsel",
        "One line description of project.",
        "Miscellaneous",
    ),
]


# -- Options for the InterSphinx extension ------------------------------------

intersphinx_mapping = {
    "cssselect": ("https://cssselect.readthedocs.io/en/latest", None),
    "python": ("https://docs.python.org/3", None),
    "requests": ("https://requests.kennethreitz.org/en/latest", None),
    "lxml": ("https://lxml.de/apidoc/", None),
}


# --- Nitpicking options ------------------------------------------------------

# nitpicky = True  # https://github.com/scrapy/cssselect/pull/110
nitpick_ignore = [
    ("py:class", "ExpressionError"),
    ("py:class", "SelectorSyntaxError"),
    ("py:class", "cssselect.xpath.GenericTranslator"),
    ("py:class", "cssselect.xpath.HTMLTranslator"),
    ("py:class", "cssselect.xpath.XPathExpr"),
    ("py:class", "lxml.etree.XMLParser"),
]
