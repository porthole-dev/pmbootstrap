# Copyright 2026 Stefan Hansson, Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import os

import pmb.build
from pmb.core.arch import Arch
from pmb.core.context import get_context
from pmb.helpers import logging


def build(
    packages: list[str], arch: Arch | None, code_src: str, use_envkernel: bool, use_strict: bool
) -> None:
    # Strict mode: zap everything
    if use_strict:
        pmb.chroot.zap(False)

    if use_envkernel:
        pmb.build.envkernel.package_kernel(packages)
        return

    # Set src and force
    src = os.path.realpath(os.path.expanduser(code_src[0])) if code_src else None
    force = True if src else get_context().force
    if src and not os.path.exists(src):
        raise RuntimeError("Invalid path specified for --src: " + src)

    context = get_context()
    # Build all packages
    built = pmb.build.packages(context, packages, arch, force, strict=use_strict, src=src)

    # Notify about packages that weren't built
    for package in set(packages) - set(built):
        logging.info(
            "NOTE: Package '" + package + "' is up to date. Use"
            " 'pmbootstrap build " + package + " --force'"
            " if needed."
        )
