# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import collections
from typing import Any
from collections.abc import Sequence
from pmb.core.arch import Arch
from pmb.core.context import get_context
from pmb.helpers import logging
from pathlib import Path
import tarfile
import pmb.chroot.apk
import pmb.helpers.package
import pmb.helpers.repo
import pmb.parse.version

apkindex_map = {
    "A": "arch",
    "D": "depends",
    "o": "origin",
    "P": "pkgname",
    "p": "provides",
    "k": "provider_priority",
    "t": "timestamp",
    "V": "version",
}

required_apkindex_keys = ["arch", "pkgname", "version"]


def parse_next_block(path: Path, lines: list[str]):
    """Parse the next block in an APKINDEX.

    :param path: to the APKINDEX.tar.gz
    :param start: current index in lines, gets increased in this
                  function. Wrapped into a list, so it can be modified
                  "by reference". Example: [5]
    :param lines: all lines from the "APKINDEX" file inside the archive
    :returns: dictionary with the following structure:
              ``{ "arch": "noarch", "depends": ["busybox-extras", "lddtree", ... ],
              "origin": "postmarketos-mkinitfs",
              "pkgname": "postmarketos-mkinitfs",
              "provides": ["mkinitfs=0.0.1"],
              "timestamp": "1500000000",
              "version": "0.0.4-r10" }``

              NOTE: "depends" is not set for packages without any dependencies, e.g. ``musl``.

              NOTE: "timestamp" and "origin" are not set for virtual packages (#1273).
              We use that information to skip these virtual packages in parse().
    :returns: None, when there are no more blocks
    """
    # Parse until we hit an empty line or end of file
    ret: dict[str, Any] = {}
    required_found = 0  # Count the required keys we found
    line = ""
    while len(lines):
        # We parse backwards for performance (pop(0) is super slow)
        line = lines.pop()
        if not line:
            continue
        # Parse keys from the mapping
        k = line[0]
        key = apkindex_map.get(k, None)

        # The checksum key is always the FIRST in the block, so when we find
        # it we know we're done.
        if k == "C":
            break
        if key:
            if key in ret:
                raise RuntimeError(f"Key {key} specified twice in block: {ret}, file: {path}")
            if key in required_apkindex_keys:
                required_found += 1
            ret[key] = line[2:]

    # Format and return the block
    if not len(lines) and not ret:
        return None

    # Check for required keys
    if required_found != len(required_apkindex_keys):
        for key in required_apkindex_keys:
            if key not in ret:
                raise RuntimeError(f"Missing required key '{key}' in block " f"{ret}, file: {path}")
        raise RuntimeError(
            f"Expected {len(required_apkindex_keys)} required keys,"
            f" but found {required_found} in block: {ret}, file: {path}"
        )

    # Format optional lists
    for key in ["provides", "depends"]:
        if key in ret and ret[key] != "":
            # Ignore all operators for now
            values = ret[key].split(" ")
            ret[key] = []
            for value in values:
                for operator in [">", "=", "<", "~"]:
                    if operator in value:
                        value = value.split(operator)[0]
                        break
                ret[key].append(value)
        else:
            ret[key] = []
    return ret


def parse_add_block(ret, block, alias=None, multiple_providers=True):
    """Add one block to the return dictionary of parse().

    :param ret: dictionary of all packages in the APKINDEX that is
                getting built right now. This function will extend it.
    :param block: return value from parse_next_block().
    :param alias: defaults to the pkgname, could be an alias from the
                  "provides" list.
    :param multiple_providers: assume that there are more than one provider for
                               the alias. This makes sense when parsing the
                               APKINDEX files from a repository (#1122), but
                               not when parsing apk's installed packages DB.
    """
    # Defaults
    pkgname = block["pkgname"]
    alias = alias or pkgname

    # Get an existing block with the same alias
    block_old = None
    if multiple_providers and alias in ret and pkgname in ret[alias]:
        block_old = ret[alias][pkgname]
    elif not multiple_providers and alias in ret:
        block_old = ret[alias]

    # Ignore the block, if the block we already have has a higher version
    if block_old:
        version_old = block_old["version"]
        version_new = block["version"]
        if pmb.parse.version.compare(version_old, version_new) == 1:
            return

    # Add it to the result set
    if multiple_providers:
        if alias not in ret:
            ret[alias] = {}
        ret[alias][pkgname] = block
    else:
        ret[alias] = block


def parse(path: Path, multiple_providers=True):
    r"""Parse an APKINDEX.tar.gz file, and return its content as dictionary.

    :param path: path to an APKINDEX.tar.gz file or apk package database
                 (almost the same format, but not compressed).
    :param multiple_providers: assume that there are more than one provider for
                               the alias. This makes sense when parsing the
                               APKINDEX files from a repository (#1122), but
                               not when parsing apk's installed packages DB.
    :returns: (without multiple_providers)

    Generic format:
        ``{ pkgname: block, ... }``

    Example:
        ``{ "postmarketos-mkinitfs": block, "so:libGL.so.1": block, ...}``

    :returns: (with multiple_providers)

    Generic format:
        ``{ provide: { pkgname: block, ... }, ... }``

    Example:
        ``{ "postmarketos-mkinitfs": {"postmarketos-mkinitfs": block},"so:libGL.so.1": {"mesa-egl": block, "libhybris": block}, ...}``

    *NOTE:* ``block`` is the return value from ``parse_next_block()`` above.

    """
    # Require the file to exist
    if not path.is_file():
        logging.verbose(
            "NOTE: APKINDEX not found, assuming no binary packages"
            f" exist for that architecture: {path}"
        )
        return {}

    # Try to get a cached result first
    lastmod = path.lstat().st_mtime
    _cache_key = "multiple" if multiple_providers else "single"
    key = cache_key(path)
    if key in pmb.helpers.other.cache["apkindex"]:
        cache = pmb.helpers.other.cache["apkindex"][key]
        if cache["lastmod"] == lastmod:
            if _cache_key in cache:
                return cache[_cache_key]
        else:
            clear_cache(path)

    # Read all lines
    lines: Sequence[str]
    if tarfile.is_tarfile(path):
        with tarfile.open(path, "r:gz") as tar:
            with tar.extractfile(tar.getmember("APKINDEX")) as handle:  # type:ignore[union-attr]
                lines = handle.read().decode().splitlines()
    else:
        with path.open("r", encoding="utf-8") as handle:
            lines = handle.read().splitlines()

    # The APKINDEX might be empty, for example if you run "pmbootstrap index" and have no local
    # packages
    if not lines:
        return {}

    # Parse the whole APKINDEX file
    ret: dict[str, Any] = collections.OrderedDict()
    if lines[-1] == "\n":
        lines.pop()  # Strip the trailing newline
    while True:
        block = parse_next_block(path, lines)
        if not block:
            break

        # Skip virtual packages
        if "timestamp" not in block:
            logging.verbose(f"Skipped virtual package {block} in" f" file: {path}")
            continue

        # Add the next package and all aliases
        parse_add_block(ret, block, None, multiple_providers)
        if "provides" in block:
            for alias in block["provides"]:
                parse_add_block(ret, block, alias, multiple_providers)

    # Update the cache
    key = cache_key(path)
    if key not in pmb.helpers.other.cache["apkindex"]:
        pmb.helpers.other.cache["apkindex"][key] = {"lastmod": lastmod}
    pmb.helpers.other.cache["apkindex"][key][_cache_key] = ret
    return ret


def parse_blocks(path: Path):
    """
    Read all blocks from an APKINDEX.tar.gz into a list.

    :path: full path to the APKINDEX.tar.gz file.
    :returns: all blocks in the APKINDEX, without restructuring them by
              pkgname or removing duplicates with lower versions (use
              parse() if you need these features). Structure:
              ``[block, block, ...]``

    NOTE: "block" is the return value from parse_next_block() above.
    """
    # Parse all lines
    with tarfile.open(path, "r:gz") as tar:
        with tar.extractfile(tar.getmember("APKINDEX")) as handle:  # type:ignore[union-attr]
            lines = handle.read().decode().splitlines()

    # Parse lines into blocks
    ret: list[str] = []
    while True:
        block = pmb.parse.apkindex.parse_next_block(path, lines)
        if not block:
            return ret
        ret.append(block)


def cache_key(path: Path):
    return str(path.relative_to(get_context().config.work))


def clear_cache(path: Path):
    """
    Clear the APKINDEX parsing cache.

    :returns: True on successful deletion, False otherwise
    """
    key = cache_key(path)
    logging.verbose(f"Clear APKINDEX cache for: {key}")
    if key in pmb.helpers.other.cache["apkindex"]:
        del pmb.helpers.other.cache["apkindex"][key]
        return True
    else:
        logging.verbose(
            "Nothing to do, path was not in cache:"
            + str(pmb.helpers.other.cache["apkindex"].keys())
        )
        return False


def providers(package, arch: Arch | None = None, must_exist=True, indexes=None):
    """
    Get all packages, which provide one package.

    :param package: of which you want to have the providers
    :param arch: defaults to native arch, only relevant for indexes=None
    :param must_exist: When set to true, raise an exception when the package is
                       not provided at all.
    :param indexes: list of APKINDEX.tar.gz paths, defaults to all index files
                    (depending on arch)
    :returns: list of parsed packages. Example for package="so:libGL.so.1":
        ``{"mesa-egl": block, "libhybris": block}``
        block is the return value from parse_next_block() above.
    """
    if not indexes:
        indexes = pmb.helpers.repo.apkindex_files(arch)

    package = pmb.helpers.package.remove_operators(package)

    ret: dict[str, Any] = collections.OrderedDict()
    for path in indexes:
        # Skip indexes not providing the package
        index_packages = parse(path)
        if package not in index_packages:
            continue

        # Iterate over found providers
        for provider_pkgname, provider in index_packages[package].items():
            # Skip lower versions of providers we already found
            version = provider["version"]
            if provider_pkgname in ret:
                version_last = ret[provider_pkgname]["version"]
                if pmb.parse.version.compare(version, version_last) == -1:
                    logging.verbose(
                        f"{package}: provided by: {provider_pkgname}-{version}"
                        f"in {path} (but {version_last} is higher)"
                    )
                    continue

            # Add the provider to ret
            logging.verbose(f"{package}: provided by: {provider_pkgname}-{version} in {path}")
            ret[provider_pkgname] = provider

    if ret == {} and must_exist:
        import os

        logging.debug(f"Searched in APKINDEX files: {', '.join([os.fspath(x) for x in indexes])}")
        raise RuntimeError("Could not find package '" + package + "'!")

    return ret


def provider_highest_priority(providers, pkgname):
    """Get the provider(s) with the highest provider_priority and log a message.

    :param providers: returned dict from providers(), must not be empty
    :param pkgname: the package name we are interested in (for the log message)
    """
    max_priority = 0
    priority_providers: collections.OrderedDict[str, str] = collections.OrderedDict()
    for provider_name, provider in providers.items():
        priority = int(provider.get("provider_priority", -1))
        if priority > max_priority:
            priority_providers.clear()
            max_priority = priority
        if priority == max_priority:
            priority_providers[provider_name] = provider

    if priority_providers:
        logging.debug(
            f"{pkgname}: picked provider(s) with highest priority "
            f"{max_priority}: {', '.join(priority_providers.keys())}"
        )
        return priority_providers

    # None of the providers seems to have a provider_priority defined
    return providers


def provider_shortest(providers, pkgname):
    """Get the provider with the shortest pkgname and log a message. In most cases
    this should be sufficient, e.g. 'mesa-purism-gc7000-egl, mesa-egl' or
    'gtk+2.0-maemo, gtk+2.0'.

    :param providers: returned dict from providers(), must not be empty
    :param pkgname: the package name we are interested in (for the log message)
    """
    ret = min(list(providers.keys()), key=len)
    if len(providers) != 1:
        logging.debug(
            f"{pkgname}: has multiple providers ("
            f"{', '.join(providers.keys())}), picked shortest: {ret}"
        )
    return providers[ret]


def package(package, arch: Arch | None = None, must_exist=True, indexes=None):
    """
    Get a specific package's data from an apkindex.

    :param package: of which you want to have the apkindex data
    :param arch: defaults to native arch, only relevant for indexes=None
    :param must_exist: When set to true, raise an exception when the package is
                       not provided at all.
    :param indexes: list of APKINDEX.tar.gz paths, defaults to all index files
                    (depending on arch)
    :returns: a dictionary with the following structure:
              { "arch": "noarch",
              "depends": ["busybox-extras", "lddtree", ... ],
              "pkgname": "postmarketos-mkinitfs",
              "provides": ["mkinitfs=0.0.1"],
              "version": "0.0.4-r10" }
              or None when the package was not found.
    """
    # Provider with the same package
    package_providers = providers(package, arch, must_exist, indexes)
    if package in package_providers:
        return package_providers[package]

    # Any provider
    if package_providers:
        return pmb.parse.apkindex.provider_shortest(package_providers, package)

    # No provider
    if must_exist:
        raise RuntimeError("Package '" + package + "' not found in any" " APKINDEX.")
    return None
