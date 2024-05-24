# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

class Command():
    """Base class for pmbootstrap commands."""

    def run(self):
        """Run the command."""
        raise NotImplementedError()
