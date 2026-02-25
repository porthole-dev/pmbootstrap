# Copyright 2024 Stefan Hansson
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

from dataclasses import dataclass

import pmb.build._package
from pmb.core.apkindex_block import ApkindexBlock
from pmb.core.context import get_context
from pmb.types import Apkbuild


@dataclass
class PackageMetadata:
    # This can't be list[Arch] because it can have values like "noarch" and "!armhf"
    arch: list[str]
    depends: list[str]
    pkgname: str
    provides: list[str]
    version: str
    from_pmaports: bool

    @staticmethod
    def from_apkindex_block(apkindex_block: ApkindexBlock) -> PackageMetadata:
        return PackageMetadata(
            arch=[str(apkindex_block.arch)],
            depends=apkindex_block.depends,
            pkgname=apkindex_block.pkgname,
            provides=apkindex_block.provides,
            version=apkindex_block.version,
            from_pmaports=False,
        )

    @staticmethod
    def from_pmaport(pmaport: Apkbuild) -> PackageMetadata:
        pmaport_arches = pmaport["arch"]
        pmaport_depends = pmb.build._package.get_depends(get_context(), pmaport)
        pmaport_pkgname = pmaport["pkgname"]
        pmaport_provides = pmaport["provides"]
        pmaport_version = pmaport["pkgver"] + "-r" + pmaport["pkgrel"]

        return PackageMetadata(
            arch=pmaport_arches,
            depends=pmaport_depends or [],
            pkgname=pmaport_pkgname,
            provides=pmaport_provides,
            version=pmaport_version,
            from_pmaports=True,
        )
