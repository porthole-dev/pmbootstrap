# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

from pmb.core.chroot import Chroot, ChrootType
from pmb.core.context import Context

__context: Context

def get_context() -> Context:
    """Get immutable global runtime context."""
    global __context

    # We must defer this to first call to avoid
    # circular imports.
    if "__context" not in globals():
        __context = Context()
    return __context
