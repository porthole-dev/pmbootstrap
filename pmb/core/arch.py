# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import annotations

import enum
from pathlib import Path, PosixPath, PurePosixPath
import platform

# Initialised at the bottom
_cached_native_arch: Arch


class Arch(enum.Enum):
    """Supported architectures according to the Alpine
    APKBUILD format."""

    x86 = "x86"
    x86_64 = "x86_64"
    armhf = "armhf"
    armv7 = "armv7"
    aarch64 = "aarch64"
    riscv64 = "riscv64"
    s390x = "s390x"
    ppc64le = "ppc64le"
    # Arches Alpine can build for
    armel = "armel"
    loongarch32 = "loongarch32"
    loongarchx32 = "loongarchx32"
    loongarch64 = "loongarch64"
    mips = "mips"
    mips64 = "mips64"
    mipsel = "mipsel"
    mips64el = "mips64el"
    noarch = "noarch"
    ppc = "ppc"
    ppc64 = "ppc64"
    riscv32 = "riscv32"

    def __str__(self) -> str:
        return self.value

    @staticmethod
    def from_str(arch: str) -> Arch:
        try:
            return Arch(arch)
        except ValueError:
            raise ValueError(
                f"Invalid architecture: '{arch}',"
                " expected something like:"
                f" {', '.join(sorted(str(a) for a in Arch.supported()))}"
            )

    @staticmethod
    def from_machine_type(machine_type: str) -> Arch:
        match machine_type:
            case "i686":
                return Arch.x86
            case "x86_64":
                return Arch.x86_64
            case "aarch64":
                return Arch.aarch64
            case "armv6l":
                return Arch.armhf
            case "armv7l" | "armv8l":
                return Arch.armv7
            case _:
                raise ValueError(f"Unsupported machine type '{machine_type}'")

    @staticmethod
    def native() -> Arch:
        global _cached_native_arch
        return _cached_native_arch

    def is_native(self) -> bool:
        return self == Arch.native()

    @staticmethod
    def supported() -> set[Arch]:
        """Officially supported host/target architectures for postmarketOS. Only
        specify architectures supported by Alpine here. For cross-compiling,
        we need to generate the "musl-$ARCH" and "gcc-$ARCH" packages (use
        "pmbootstrap aportgen musl-armhf" etc.)."""
        # FIXME: cache?
        return set(
            [
                Arch.armhf,
                Arch.armv7,
                Arch.aarch64,
                Arch.x86_64,
                Arch.x86,
                Arch.riscv64,
                Arch.ppc64le,
                Arch.native(),
            ]
        )

    def kernel(self) -> str:
        match self:
            case Arch.x86:
                return "x86"
            case Arch.x86_64:
                return "x86_64"
            case Arch.armhf | Arch.armv7:
                return "arm"
            case Arch.aarch64:
                return "arm64"
            case Arch.riscv64:
                return "riscv"
            case Arch.ppc64le | Arch.ppc64 | Arch.ppc:
                return "powerpc"
            case Arch.s390x:
                return "s390"
            case _:
                return self.value

    def qemu(self) -> str:
        match self:
            case Arch.x86:
                return "i386"
            case Arch.armhf | Arch.armv7:
                return "arm"
            case Arch.ppc64le:
                return "ppc64"
            case _:
                return self.value

    def alpine_triple(self) -> str:
        """Get the cross compiler triple for this architecture on Alpine."""
        match self:
            case Arch.aarch64:
                return "aarch64-alpine-linux-musl"
            case Arch.armel:
                return "armv5-alpine-linux-musleabi"
            case Arch.armhf:
                return "armv6-alpine-linux-musleabihf"
            case Arch.armv7:
                return "armv7-alpine-linux-musleabihf"
            case Arch.loongarch32:
                return "loongarch32-alpine-linux-musl"
            case Arch.loongarchx32:
                return "loongarchx32-alpine-linux-musl"
            case Arch.loongarch64:
                return "loongarch64-alpine-linux-musl"
            case Arch.mips:
                return "mips-alpine-linux-musl"
            case Arch.mips64:
                return "mips64-alpine-linux-musl"
            case Arch.mipsel:
                return "mipsel-alpine-linux-musl"
            case Arch.mips64el:
                return "mips64el-alpine-linux-musl"
            case Arch.ppc:
                return "powerpc-alpine-linux-musl"
            case Arch.ppc64:
                return "powerpc64-alpine-linux-musl"
            case Arch.ppc64le:
                return "powerpc64le-alpine-linux-musl"
            case Arch.riscv32:
                return "riscv32-alpine-linux-musl"
            case Arch.riscv64:
                return "riscv64-alpine-linux-musl"
            case Arch.s390x:
                return "s390x-alpine-linux-musl"
            case Arch.x86:
                return "i586-alpine-linux-musl"
            case Arch.x86_64:
                return "x86_64-alpine-linux-musl"
            case _:
                raise ValueError(
                    f"Can not map Alpine architecture '{self}' to the right hostspec value"
                )

    def cpu_emulation_required(self) -> bool:
        # Obvious case: host arch is target arch
        if self == Arch.native():
            return False

        # Other cases: host arch on the left, target archs on the right
        not_required = {
            Arch.x86_64: [Arch.x86],
            Arch.armv7: [Arch.armel, Arch.armhf],
            Arch.aarch64: [Arch.armv7],
        }
        if Arch.native() in not_required:
            if self in not_required[Arch.native()]:
                return False

        # No match: then it's required
        return True

    # Magic to let us use an arch as a Path element
    def __truediv__(self, other: object) -> Path:
        if isinstance(other, PosixPath) or isinstance(other, PurePosixPath):
            # Convert the other path to a relative path
            # FIXME: we should avoid creating absolute paths that we actually want
            # to make relative to the chroot...
            # if other.is_absolute():
            #   logging.warning("FIXME: absolute path made relative to Arch??")
            other = other.relative_to("/") if other.is_absolute() else other
            return Path(str(self)).joinpath(other)
        if isinstance(other, str):
            # Let's us do Arch / "whatever.apk" and magically produce a path
            # maybe this is a pattern we should avoid, but it seems somewhat
            # sensible
            return Path(str(self)).joinpath(other.strip("/"))

        return NotImplemented

    def __rtruediv__(self, other: object) -> Path:
        if isinstance(other, PosixPath) or isinstance(other, PurePosixPath):
            # Important to produce a new Path object here, otherwise we
            # end up with one object getting shared around and modified
            # and lots of weird stuff happens.
            return Path(other) / str(self)
        # We don't support str / Arch since that is a weird pattern

        return NotImplemented


_cached_native_arch = Arch.from_machine_type(platform.machine())
