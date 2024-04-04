# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations
import enum
from typing import Generator, Optional
from pathlib import Path, PosixPath, PurePosixPath
import pmb.config

class ChrootType(enum.Enum):
    ROOTFS = "rootfs"
    BUILDROOT = "buildroot"
    INSTALLER = "installer"
    NATIVE = "native"

    def __str__(self) -> str:
        return self.name

class Chroot:
    __type: ChrootType
    __name: str

    def __init__(self, suffix_type: ChrootType, name: Optional[str] = ""):
        self.__type = suffix_type
        self.__name = name or ""
        
        self.__validate()

    def __validate(self) -> None:
        """
        Ensures that this suffix follows the correct format.
        """
        valid_arches = [
            "x86",
            "x86_64",
            "aarch64",
            "armhf", # XXX: remove this?
            "armv7",
            "riscv64",
        ]

        # A buildroot suffix must have a name matching one of alpines
        # architectures.
        if self.__type == ChrootType.BUILDROOT and self.__name not in valid_arches:
            raise ValueError(f"Invalid buildroot suffix: '{self.__name}'")

        # A rootfs or installer suffix must have a name matching a device.
        if self.__type == ChrootType.INSTALLER or self.__type == ChrootType.ROOTFS:
            # FIXME: pmb.helpers.devices.find_path() requires args parameter
            pass

        # A native suffix must not have a name.
        if self.__type == ChrootType.NATIVE and self.__name != "":
            raise ValueError(f"The native suffix can't have a name but got: "
                             f"'{self.__name}'")


    def __str__(self) -> str:
        if len(self.__name) > 0:
            return f"{self.__type.value}_{self.__name}"
        else:
            return self.__type.value


    @property
    def dirname(self) -> str:
        return f"chroot_{self}"


    @property
    def path(self) -> Path:
        return Path(pmb.config.work, self.dirname)


    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return str(self) == other or self.path == Path(other) or self.name() == other

        if isinstance(other, PosixPath):
            return self.path == other

        if not isinstance(other, Chroot):
            return NotImplemented

        return self.type() == other.type() and self.name() == other.name()


    def __truediv__(self, other: object) -> Path:
        if isinstance(other, PosixPath) or isinstance(other, PurePosixPath):
            # Convert the other path to a relative path
            # FIXME: we should avoid creating absolute paths that we actually want
            # to make relative to the chroot...
            other = other.relative_to("/") if other.is_absolute() else other
            return self.path.joinpath(other)
        if isinstance(other, str):
            return self.path.joinpath(other.strip("/"))

        return NotImplemented


    def __rtruediv__(self, other: object) -> Path:
        if isinstance(other, PosixPath) or isinstance(other, PurePosixPath):
            return Path(other) / self.path
        if isinstance(other, str):
            return other / self.path

        return NotImplemented


    def type(self) -> ChrootType:
        return self.__type


    def name(self) -> str:
        return self.__name


    @staticmethod
    def native() -> Chroot:
        return Chroot(ChrootType.NATIVE)


    @staticmethod
    def buildroot(arch: str) -> Chroot:
        return Chroot(ChrootType.BUILDROOT, arch)


    @staticmethod
    def rootfs(device: str) -> Chroot:
        return Chroot(ChrootType.ROOTFS, device)


    @staticmethod
    def from_str(s: str) -> Chroot:
        """
        Generate a Suffix from a suffix string like "buildroot_aarch64"
        """
        parts = s.split("_", 1)
        stype = parts[0]

        if len(parts) == 2:
            # Will error if stype isn't a valid ChrootType
            # The name will be validated by the Chroot constructor
            return Chroot(ChrootType(stype), parts[1])

        # "native" is the only valid suffix type, the constructor(s)
        # will validate that stype is "native"
        return Chroot(ChrootType(stype))
    
    @staticmethod
    def iter_patterns() -> Generator[str, None, None]:
        """
        Generate suffix patterns for all valid suffix types
        """
        for stype in ChrootType:
            if stype == ChrootType.NATIVE:
                yield f"chroot_{stype.value}"
            else:
                yield f"chroot_{stype.value}_*"


    @staticmethod
    def glob() -> Generator[Path, None, None]:
        """
        Glob all initialized chroot directories
        """
        for pattern in Chroot.iter_patterns():
            yield from Path(pmb.config.work).glob(pattern)
