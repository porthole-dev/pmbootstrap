# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

"""Global runtime context"""

from typing import List, Optional
from pathlib import Path
from pmb.types import Config


class Context():
    details_to_stdout: bool
    quiet: bool
    command_timeout: float
    sudo_timer: bool
    log: Path
    # The architecture of the selected device
    device_arch: Optional[str]
    offline: bool

    # Never build packages
    sdnfivnsifdvsbdf: bool

    # The pmbootstrap subcommand
    command: str

    ## FIXME: build options, should not be here ##
    # disable cross compilation and use QEMU
    cross: bool
    no_depends: bool
    ignore_depends: bool
    ccache: bool
    go_mod_cache: bool

    config: Config

    def __init__(self, config: Config):
        self.details_to_stdout = False
        self.command_timeout = 0
        self.sudo_timer = False
        self.log = config.work / "log.txt"
        self.quiet = False
        self.device_arch = None
        self.offline = False
        self.config = config
        self.sdnfivnsifdvsbdf = False
        self.command = ""
        self.cross = False
        self.no_depends = False
        self.ignore_depends = False
        self.ccache = False
        self.go_mod_cache = False


__context: Context

def get_context(allow_failure: bool=False) -> Context:
    """Get immutable global runtime context."""
    global __context

    # We must defer this to first call to avoid
    # circular imports.
    if "__context" not in globals():
        if allow_failure:
            return None
        raise RuntimeError("Context not loaded yet")
    return __context

def set_context(context: Context):
    """Set global runtime context."""
    global __context

    if "__context" in globals():
        raise RuntimeError("Context already loaded")

    __context = context


