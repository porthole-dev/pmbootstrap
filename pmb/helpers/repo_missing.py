# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import overload, Literal

from pmb.core.arch import Arch
from pmb.helpers import logging
from pmb.types import Apkbuild

import pmb.build
import pmb.helpers.package
import pmb.helpers.pmaports


def filter_missing_packages(arch: Arch, pkgnames: list[str]) -> list[str]:
    """Create a subset of pkgnames with missing or outdated binary packages.

    :param arch: architecture (e.g. "armhf")
    :param pkgnames: list of package names (e.g. ["hello-world", "test12"])
    :returns: subset of pkgnames (e.g. ["hello-world"])
    """
    ret = []
    for pkgname in pkgnames:
        binary = pmb.parse.apkindex.package(pkgname, arch, False)
        must_exist = False if binary else True
        pmaport = pmb.helpers.pmaports.get(pkgname, must_exist)
        if pmaport and pmb.build.get_status(arch, pmaport).necessary():
            ret.append(pkgname)
    return ret


def filter_aport_packages(pkgnames: list[str]) -> list[str]:
    """Create a subset of pkgnames where each one has an aport.

    :param pkgnames: list of package names (e.g. ["hello-world", "test12"])
    :returns: subset of pkgnames (e.g. ["hello-world"])
    """
    ret = []
    for pkgname in pkgnames:
        if pmb.helpers.pmaports.find_optional(pkgname):
            ret += [pkgname]
    return ret


def filter_arch_packages(arch: Arch, pkgnames: list[str]) -> list[str]:
    """Create a subset of pkgnames with packages removed that can not be built for a certain arch.

    :param arch: architecture (e.g. "armhf")
    :param pkgnames: list of package names (e.g. ["hello-world", "test12"])
    :returns: subset of pkgnames (e.g. ["hello-world"])
    """
    ret = []
    for pkgname in pkgnames:
        if pmb.helpers.package.check_arch(pkgname, arch, False):
            ret += [pkgname]
    return ret


def get_relevant_packages(arch: Arch, pkgname: str | None = None, built: bool = False) -> list[str]:
    """Get all packages that can be built for the architecture in question.

    :param arch: architecture (e.g. "armhf")
    :param pkgname: only look at a specific package (and its dependencies)
    :param built: include packages that have already been built
    :returns: an alphabetically sorted list of pkgnames, e.g.:
        ["devicepkg-dev", "hello-world", "osk-sdl"]
    """
    if pkgname:
        if not pmb.helpers.package.check_arch(pkgname, arch, False):
            raise RuntimeError(f"{pkgname} can't be built for {arch}.")
        ret = pmb.helpers.package.depends_recurse(pkgname, arch)
    else:
        ret = pmb.helpers.pmaports.get_list()
        ret = filter_arch_packages(arch, ret)
    if built:
        ret = filter_aport_packages(ret)
        if not len(ret):
            logging.info(
                "NOTE: no aport found for any package in the"
                " dependency tree, it seems they are all provided by"
                " upstream (Alpine)."
            )
    else:
        ret = filter_missing_packages(arch, ret)
        if not len(ret):
            logging.info(
                "NOTE: all relevant packages are up to date, use"
                " --built to include the ones that have already been"
                " built."
            )

    # Sort alphabetically (to get a deterministic build order)
    ret.sort()
    return ret


def generate_output_format(arch: Arch, pkgnames: list[str]) -> list[Apkbuild]:
    """Generate the detailed output format.

    :param arch: architecture
    :param pkgnames: list of package names that should be in the output,
        e.g.: ["hello-world", "pkg-depending-on-hello-world"]
        :returns: a list like the following:
        [{"pkgname": "hello-world",
        "repo": "main",
        "version": "1-r4",
        "depends": []},
        {"pkgname": "pkg-depending-on-hello-world",
        "version": "0.5-r0",
        "repo": "main",
        "depends": ["hello-world"]}]
    """
    ret = []
    for pkgname in pkgnames:
        entry = pmb.helpers.package.get(pkgname, arch, True, try_other_arches=False)

        if entry is None:
            raise RuntimeError(f"Couldn't get package {pkgname} for arch {arch}")

        ret += [
            {
                "pkgname": entry.pkgname,
                "repo": pmb.helpers.pmaports.get_repo(pkgname),
                "version": entry.version,
                "depends": entry.depends,
            }
        ]
    return ret


@overload
def generate(
    arch: Arch, overview: Literal[False], pkgname: str | None = ..., built: bool = ...
) -> list[Apkbuild]: ...


@overload
def generate(
    arch: Arch, overview: Literal[True], pkgname: str | None = ..., built: bool = ...
) -> list[str]: ...


@overload
def generate(
    arch: Arch, overview: bool, pkgname: str | None = ..., built: bool = ...
) -> list[Apkbuild] | list[str]: ...


def generate(
    arch: Arch, overview: bool, pkgname: str | None = None, built: bool = False
) -> list[Apkbuild] | list[str]:
    """Get packages that need to be built, with all their dependencies.

    :param arch: architecture (e.g. "armhf")
    :param pkgname: only look at a specific package
    :param built: include packages that have already been built
    :returns: a list like the following:
        [{"pkgname": "hello-world", "repo": "main", "version": "1-r4"},
        {"pkgname": "package-depending-on-hello-world", "version": "0.5-r0", "repo": "main"}]
    """
    # Log message
    packages_str = pkgname if pkgname else "all packages"
    logging.info(f"Calculate packages that need to be built ({packages_str}, {arch})")

    # Order relevant packages
    ret = get_relevant_packages(arch, pkgname, built)

    # Output format
    if overview:
        return ret
    return generate_output_format(arch, ret)
