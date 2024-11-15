# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
"""Functions that work with both pmaports and binary package repos.

See also:

    - pmb/helpers/pmaports.py (work with pmaports)

    - pmb/helpers/repo.py (work with binary package repos)
"""

from typing import overload
from pmb.core.arch import Arch
from pmb.core.package_metadata import PackageMetadata
from pmb.helpers import logging
import pmb.build._package

from pmb.meta import Cache
import pmb.helpers.pmaports
import pmb.helpers.repo


def remove_operators(package: str) -> str:
    for operator in [">", ">=", "<=", "=", "<", "~"]:
        if operator in package:
            package = package.split(operator)[0]
            break
    return package


@overload
def get(pkgname: str, arch: Arch, replace_subpkgnames: bool = ...) -> PackageMetadata: ...


@overload
def get(
    pkgname: str, arch: Arch, replace_subpkgnames: bool = ..., must_exist: bool = ...
) -> PackageMetadata | None: ...


@overload
def get(
    pkgname: str,
    arch: Arch,
    replace_subpkgnames: bool = ...,
    must_exist: bool = ...,
    try_other_arches: bool = ...,
) -> PackageMetadata | None: ...


@Cache("pkgname", "arch", "replace_subpkgnames", "try_other_arches")
def get(
    pkgname: str,
    arch: Arch,
    replace_subpkgnames: bool = False,
    must_exist: bool = True,
    try_other_arches: bool = True,
) -> PackageMetadata | None:
    """Find a package in pmaports, and as fallback in the APKINDEXes of the binary packages.

    :param pkgname: package name (e.g. "hello-world")
    :param arch: preferred architecture of the binary package.
        When it can't be found for this arch, we'll still look for another arch to see whether the
        package exists at all. So make sure to check the returned arch against what you wanted
        with check_arch(). Example: "armhf"
    :param replace_subpkgnames: replace all subpkgnames with their main pkgnames in the depends
        (see #1733)
    :param must_exist: raise an exception, if not found
    :param try_other_arches: set to False to not attempt to find other arches

    :returns: * data from the parsed APKBUILD or APKINDEX in the following format:
                    {"arch": ["noarch"], "depends": ["busybox-extras", "lddtree", ...],
                    "pkgname": "postmarketos-mkinitfs", "provides": ["mkinitfs=0..1"],
                    "version": "0.0.4-r10"}

        * None if the package was not found
    """
    # Find in pmaports
    ret: PackageMetadata | None = None
    pmaport = pmb.helpers.pmaports.get(pkgname, False)
    if pmaport:
        ret = PackageMetadata.from_pmaport(pmaport)

    # Find in APKINDEX (given arch)
    if not ret or not pmb.helpers.pmaports.check_arches(ret.arch, arch):
        pmb.helpers.repo.update(arch)
        ret_repo = pmb.parse.apkindex.package(pkgname, arch, False)

        # Save as result if there was no pmaport, or if the pmaport can not be
        # built for the given arch, but there is a binary package for that arch
        # (e.g. temp/mesa can't be built for x86_64, but Alpine has it)
        if ret_repo and (not ret or ret_repo.arch == arch):
            ret = PackageMetadata.from_apkindex_block(ret_repo)

    # Find in APKINDEX (other arches)
    if not ret and try_other_arches:
        pmb.helpers.repo.update()
        for arch_i in Arch.supported():
            if arch_i != arch:
                apkindex_block = pmb.parse.apkindex.package(pkgname, arch_i, False)
                if apkindex_block is not None:
                    ret = PackageMetadata.from_apkindex_block(apkindex_block)
            if ret:
                break

    # Replace subpkgnames if desired
    if replace_subpkgnames and ret:
        depends_new = []
        for depend in ret.depends:
            depend_data = get(depend, arch, must_exist=False, try_other_arches=try_other_arches)
            if not depend_data:
                logging.warning(f"WARNING: {pkgname}: failed to resolve" f" dependency '{depend}'")
                # Can't replace potential subpkgname
                if depend not in depends_new:
                    depends_new += [depend]
                continue
            depend_pkgname = depend_data.pkgname
            if depend_pkgname not in depends_new:
                depends_new += [depend_pkgname]
        ret.depends = depends_new

    # Save to cache and return
    if ret:
        return ret

    # Could not find the package
    if not must_exist:
        return None
    raise RuntimeError(f"Package '{pkgname}': Could not find it in pmaports or any APKINDEX!")


@Cache("pkgname", "arch")
def depends_recurse(pkgname: str, arch: Arch) -> list[str]:
    """Recursively resolve all of the package's dependencies.

    :param pkgname: name of the package (e.g. "device-samsung-i9100")
    :param arch: preferred architecture for binary packages
    :returns: a list of pkgname_start and all its dependencies, e.g:
        ["busybox-static-armhf", "device-samsung-i9100",
        "linux-samsung-i9100", ...]
    """
    # Build ret (by iterating over the queue)
    queue = [pkgname]
    ret = []
    while len(queue):
        pkgname_queue = queue.pop()
        package = get(pkgname_queue, arch)

        # Add its depends to the queue
        for depend in package.depends:
            if depend not in ret:
                queue += [depend]

        # Add the pkgname (not possible subpkgname) to ret
        if package.pkgname not in ret:
            ret += [package.pkgname]
    ret.sort()

    return ret


def check_arch(pkgname: str, arch: Arch, binary: bool = True) -> bool:
    """Check if a package be built for a certain architecture, or is there a binary package for it.

    :param pkgname: name of the package
    :param arch: architecture to check against
    :param binary: set to False to only look at the pmaports, not at binary
        packages

    :returns: True when the package can be built, or there is a binary package, False otherwise
    """
    if binary:
        arches = get(pkgname, arch).arch
    else:
        arches = pmb.helpers.pmaports.get(pkgname, must_exist=True)["arch"]
    return pmb.helpers.pmaports.check_arches(arches, arch)
