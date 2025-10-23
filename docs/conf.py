# Copyright 2024 Robert Eckelmann
# SPDX-License-Identifier: GPL-3.0-or-later

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
import os
import datetime


sys.path.insert(0, os.path.abspath(".."))  # Allow modules to be found
from pmb import __version__

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pmbootstrap"
copyright = str(datetime.date.today().year) + ", postmarketOS developers"
author = "postmarketOS developers"

release = __version__
version = ".".join(release.split(".")[:3])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinxcontrib.autoprogram",
    "sphinxcontrib.jquery",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", ".venv", "README.md"]
source_suffix = [".rst", ".md"]

# -- Options for HTML output -------------------------------------------------
html_theme = "pmos"
html_theme_options = {
    "announcement": "<a class='back-to-index' href='/'>&lt;- postmarketOS Documentation Index</a>",
    "light_css_variables": {
        "color-brand-primary": "#008443",
        "color-brand-content": "#008443",
        "color-brand-visited": "#008443",
    },
    "dark_css_variables": {
        "color-brand-primary": "#008443",
        "color-brand-content": "#008443",
        "color-brand-visited": "#008443",
    },
    "source_edit_link": "https://gitlab.postmarketos.org/postmarketOS/pmbootstrap/-/blob/master/docs/{filename}",
    "top_of_page_buttons": ["edit"],
}
html_favicon = "https://postmarketos.org/static/img/favicon.ico"

# Output file base name for HTML help builder.
htmlhelp_basename = "pmbootstrapdoc"

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [("index", "pmbootstrap", "pmbootstrap Documentation", ["postmarketOS Developers"], 1)]
