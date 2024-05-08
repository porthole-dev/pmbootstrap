# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
import os
import datetime


sys.path.insert(0, os.path.abspath('..'))  # Allow modules to be found
from pmb import __version__

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme

    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pmbootstrap'
copyright = str(datetime.date.today().year) + ', postmarketOS developers'
author = 'postmarketOS developers'

release = __version__
version = '.'.join(release.split('.')[:3])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.autosummary', 'sphinx.ext.doctest', 'sphinxcontrib.autoprogram']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_favicon = 'https://wiki.postmarketos.org/favicon.ico'

html_theme_options = {'style_nav_header_background': '008b69',}

# Output file base name for HTML help builder.
htmlhelp_basename = 'pmboostrapdoc'

html_theme_options = {
    'display_version': True,
    'style_external_links': True,
    }

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'pmbootstrap', 'pmbootstrap Documentation',
     ['postmarketOS Developers'], 1)
]
