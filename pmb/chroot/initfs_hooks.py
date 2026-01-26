# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
from collections.abc import Generator
from pathlib import Path

import pmb.chroot.apk
import pmb.config
import pmb.parse._apkbuild
from pmb.core import Chroot
from pmb.core.pkgrepo import pkgrepo_iglob
from pmb.helpers import logging
from pmb.helpers.exceptions import NonBugError


def path_to_hook_name(path: Path) -> str:
    return path.name[len(pmb.config.initfs_hook_prefix) :]


def list_chroot(suffix: Chroot, remove_prefix: bool = True) -> list[str]:
    ret = []
    prefix = pmb.config.initfs_hook_prefix
    for pkgname in pmb.chroot.apk.installed(suffix):
        if pkgname.startswith(prefix):
            if remove_prefix:
                ret.append(pkgname[len(prefix) :])
            else:
                ret.append(pkgname)
    return ret


def list_hook_paths() -> Generator[Path, None, None]:
    return pkgrepo_iglob(f"*/{pmb.config.initfs_hook_prefix}*")


def list_hook_packages() -> list[str]:
    return [path_to_hook_name(path) for path in list_hook_paths()]


def ls(suffix: Chroot) -> None:
    hooks_chroot = list_chroot(suffix)

    for hook_path in list_hook_paths():
        hook_desc = pmb.parse._apkbuild.apkbuild(hook_path)["pkgdesc"]
        hook = path_to_hook_name(hook_path)
        line = f"* {hook}: {hook_desc} ({'' if hook in hooks_chroot else 'not '}installed)"
        logging.info(line)


def add(hook: str, suffix: Chroot) -> None:
    if hook not in list_hook_packages():
        raise NonBugError(
            "Invalid hook name! Run 'pmbootstrap initfs hook_ls' to get a list of all hooks."
        )
    prefix = pmb.config.initfs_hook_prefix
    pmb.chroot.apk.install([f"{prefix}{hook}"], suffix)


def delete(hook: str, suffix: Chroot) -> None:
    if hook not in list_chroot(suffix):
        raise NonBugError("There is no such hook installed!")
    prefix = pmb.config.initfs_hook_prefix
    pmb.helpers.apk.run(["del", f"{prefix}{hook}"], suffix)


def update(suffix: Chroot) -> None:
    """Rebuild and update all hooks that are out of date"""
    pmb.chroot.apk.install(list_chroot(suffix, False), suffix)
