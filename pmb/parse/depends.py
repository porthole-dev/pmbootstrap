# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
from typing import Dict, List, Sequence, Set
from pmb.helpers import logging
import pmb.chroot
import pmb.chroot.apk
import pmb.helpers.pmaports
import pmb.parse.apkindex
from pmb.core import Chroot
from pmb.core.context import get_context


def package_from_aports(pkgname_depend):
    """
    :returns: None when there is no aport, or a dict with the keys pkgname,
              depends, version. The version is the combined pkgver and pkgrel.
    """
    # Get the aport
    aport = pmb.helpers.pmaports.find_optional(pkgname_depend)
    if not aport:
        return None

    # Parse its version
    apkbuild = pmb.parse.apkbuild(aport / "APKBUILD")
    pkgname = apkbuild["pkgname"]
    version = apkbuild["pkgver"] + "-r" + apkbuild["pkgrel"]

    # Return the dict
    logging.verbose(
        f"{pkgname_depend}: provided by: {pkgname}-{version} in {aport}")
    return {"pkgname": pkgname,
            "depends": apkbuild["depends"],
            "version": version}


def package_provider(pkgname, pkgnames_install, suffix: Chroot=Chroot.native()):
    """
    :param pkgnames_install: packages to be installed
    :returns: a block from the apkindex: {"pkgname": "...", ...}
              or None (no provider found)
    """
    # Get all providers
    arch = suffix.arch
    providers = pmb.parse.apkindex.providers(pkgname, arch, False)

    # 0. No provider
    if len(providers) == 0:
        return None

    # 1. Only one provider
    logging.verbose(f"{pkgname}: provided by: {', '.join(providers)}")
    if len(providers) == 1:
        return list(providers.values())[0]

    # 2. Provider with the same package name
    if pkgname in providers:
        logging.verbose(f"{pkgname}: choosing package of the same name as "
                        "provider")
        return providers[pkgname]

    # 3. Pick a package that will be installed anyway
    for provider_pkgname, provider in providers.items():
        if provider_pkgname in pkgnames_install:
            logging.verbose(f"{pkgname}: choosing provider '{provider_pkgname}"
                            "', because it will be installed anyway")
            return provider

    # 4. Pick a package that is already installed
    installed = pmb.chroot.apk.installed(suffix)
    for provider_pkgname, provider in providers.items():
        if provider_pkgname in installed:
            logging.verbose(f"{pkgname}: choosing provider '{provider_pkgname}"
                            f"', because it is installed in the '{suffix}' "
                            "chroot already")
            return provider

    # 5. Pick an explicitly selected provider
    provider_pkgname = get_context().config.providers.get(pkgname, "")
    if provider_pkgname in providers:
        logging.verbose(f"{pkgname}: choosing provider '{provider_pkgname}', "
                        "because it was explicitly selected.")
        return providers[provider_pkgname]

    # 6. Pick the provider(s) with the highest priority
    providers = pmb.parse.apkindex.provider_highest_priority(
        providers, pkgname)
    if len(providers) == 1:
        return list(providers.values())[0]

    # 7. Pick the shortest provider. (Note: Normally apk would fail here!)
    return pmb.parse.apkindex.provider_shortest(providers, pkgname)


def package_from_index(pkgname_depend, pkgnames_install, package_aport,
                       suffix: Chroot=Chroot.native()):
    """
    :returns: None when there is no aport and no binary package, or a dict with
              the keys pkgname, depends, version from either the aport or the
              binary package provider.
    """
    # No binary package
    provider = package_provider(pkgname_depend, pkgnames_install, suffix)
    if not provider:
        return package_aport

    # Binary package outdated
    if (package_aport and pmb.parse.version.compare(package_aport["version"],
                                                    provider["version"]) == 1):
        logging.verbose(pkgname_depend + ": binary package is outdated")
        return package_aport

    # Binary up to date (#893: overrides aport, so we have sonames in depends)
    if package_aport:
        logging.verbose(pkgname_depend + ": binary package is"
                        " up to date, using binary dependencies"
                        " instead of the ones from the aport")
    return provider
