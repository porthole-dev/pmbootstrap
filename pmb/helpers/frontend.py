# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import pmb.chroot.other
import pmb.parse
from pmb.core import Chroot, ChrootType
from pmb.core.arch import Arch
from pmb.core.context import get_context
from pmb.types import PmbArgs


def _parse_flavor(device: str, autoinstall: bool = True) -> str:
    """
    Verify the flavor argument if specified, or return a default value.

    :param autoinstall: make sure that at least one kernel flavor is installed
    """
    # Install a kernel and get its "flavor", where flavor is a pmOS-specific
    # identifier that is typically in the form
    # "postmarketos-<manufacturer>-<device/chip>", e.g.
    # "postmarketos-qcom-sdm845"
    chroot = Chroot(ChrootType.ROOTFS, device)
    flavor = pmb.chroot.other.kernel_flavor_installed(chroot, autoinstall)

    if not flavor:
        raise RuntimeError(
            f"No kernel flavors installed in chroot '{chroot}'! Please let"
            " your device package depend on a package starting with 'linux-'."
        )
    return flavor


def _parse_suffix(args: PmbArgs) -> Chroot:
    deviceinfo = pmb.parse.deviceinfo()
    if getattr(args, "image", None):
        rootfs = Chroot.native() / f"home/pmos/rootfs/{deviceinfo.codename}.img"
        return Chroot(ChrootType.IMAGE, str(rootfs))
    if getattr(args, "rootfs", None):
        return Chroot(ChrootType.ROOTFS, get_context().config.device)
    elif args.buildroot:
        if args.buildroot == "device":
            return Chroot.buildroot(deviceinfo.arch)
        else:
            return Chroot.buildroot(Arch.from_str(args.buildroot))
    elif args.suffix:
        (t_, s) = args.suffix.split("_")
        t: ChrootType = ChrootType(t_)
        return Chroot(t, s)
    else:
        return Chroot(ChrootType.NATIVE)
