# Copyright 2024 Stefan Hansson
# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import asdict, dataclass

from pmb.core.arch import Arch


@dataclass
class ApkindexBlock:
    """
    "timestamp" and "origin" are not set for virtual packages (#1273).
    We use that information to skip these virtual packages in parse().
    """

    #: the architecture of the package
    arch: Arch
    #: dependencies for the package
    depends: list[str]
    #: the origin name of the package
    origin: str | None
    #: package name
    pkgname: str
    #: what this package provides
    provides: list[str]
    #: provider priority for the package
    provider_priority: int | None
    #: unix timestamp of the package build date/time
    timestamp: str | None
    #: package version
    version: str

    @property
    def __dict__(self) -> dict:
        """This needs a manual implementation as the dataclass contains an enum."""
        block_dict = asdict(self)

        block_dict["arch"] = str(block_dict["arch"])

        return block_dict

    @__dict__.setter
    def __dict__(self, new_value: dict) -> None:
        raise AssertionError("Use dot operator access for ApkindexBlock")
