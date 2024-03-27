# Copyright 2024 Stefan "Newbyte" Hansson
# SPDX-License-Identifier: GPL-3.0-or-later


class NonBugError(Exception):
    """Exception which originates from a problem not caused by pmbootstrap's code. This
    could for example be raised if there is an error in a package pmboostrap is
    interacting with in some way."""
    pass
