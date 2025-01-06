# Copyright 2025 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
from pmb.core.arch import Arch
from pmb.core.context import get_context
from pmb.meta import Cache
from pmb.types import WithExtraRepos
from pathlib import Path

import pmb.build
import pmb.helpers.package
import pmb.helpers.pmaports
import glob
import os


@Cache("repo")
def is_abuild_forked(repo: str | None) -> bool:
    """Check if abuild is forked to make sure we build it first (pmb#2401)"""
    with_extra_repos: WithExtraRepos

    if repo == "systemd":
        with_extra_repos = "enabled"
    elif repo is None:
        with_extra_repos = "disabled"
    else:
        raise RuntimeError(f"Unexpected repo value: {repo}")

    if pmb.helpers.pmaports.find("abuild", False, False, with_extra_repos):
        return True
    return False


def generate(arch: Arch) -> list[dict[str, list[str] | str | None]]:
    """Get packages that need to be built, with all their dependencies. Include
       packages from extra-repos, no matter if systemd is enabled or not. This
       is used by bpo to fill its package database.

    :param arch: architecture (e.g. "armhf")
    :returns: a list like the following:
        [{"pkgname": "hello-world", "repo": None, "version": "1-r4"},
        {"pkgname": "package-depending-on-hello-world", "version": "0.5-r0", "repo": None}]
    """
    ret = []
    pmaports_dirs = list(map(lambda x: Path(x), get_context().config.aports))

    for pmaports_dir in pmaports_dirs:
        pattern = os.path.join(pmaports_dir, "**/*/APKBUILD")

        for apkbuild_path_str in glob.glob(pattern, recursive=True):
            apkbuild_path = Path(apkbuild_path_str)
            pkgname = apkbuild_path.parent.name

            if not pmb.helpers.package.check_arch(pkgname, arch, False):
                continue

            relpath = apkbuild_path.relative_to(pmaports_dir)
            repo = relpath.parts[1] if relpath.parts[0] == "extra-repos" else None

            entry = pmb.helpers.package.get(pkgname, arch, True, try_other_arches=False)

            if entry is None:
                raise RuntimeError(f"Couldn't get package {pkgname} for arch {arch}")

            if pkgname != "abuild" and is_abuild_forked(repo):
                entry.depends.insert(0, "abuild")

            ret += [
                {
                    "pkgname": entry.pkgname,
                    "repo": repo,
                    "version": entry.version,
                    "depends": entry.depends,
                }
            ]

    # "or -1" is needed for mypy
    # https://github.com/python/mypy/issues/9765#issuecomment-1238263745
    ret = sorted(ret, key=lambda d: d.get("pkgname") or -1)
    return ret
