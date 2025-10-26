# Copyright 2024 Robert Eckelmann
# SPDX-License-Identifier: GPL-3.0-or-later
# Configuration file for the Sphinx documentation builder.

import sys
import os
import datetime

sys.path.insert(0, os.path.abspath(".."))  # Allow modules to be found

project = "pmbootstrap"
copyright = str(datetime.date.today().year) + ", postmarketOS developers"
author = "postmarketOS developers"
exclude_patterns = ["_build", "_out", "Thumbs.db", ".DS_Store", ".venv", "README.md"]

html_theme = "pmos"
html_theme_options = {
    "source_edit_link": "https://gitlab.postmarketos.org/postmarketOS/pmbootstrap/-/blob/master/docs/{filename}",
}

# Output file base name for HTML help builder.
htmlhelp_basename = "pmbootstrapdoc"

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [("index", "pmbootstrap", "pmbootstrap Documentation", ["postmarketOS Developers"], 1)]
