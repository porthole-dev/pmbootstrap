# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import copy
import inspect
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import pmb.config
import pmb.helpers.devices
from pmb.core.arch import Arch
from pmb.core.context import get_context
from pmb.helpers import logging
from pmb.helpers.exceptions import NonBugError
from pmb.meta import Cache


class InitfsCompressionFormat(Enum):
    ZSTD = "zstd"
    LZ4 = "lz4"
    LZMA = "lzma"
    GZIP = "gzip"
    NONE = "none"

    @staticmethod
    def from_str(compression_format: str) -> InitfsCompressionFormat:
        try:
            return InitfsCompressionFormat(compression_format)
        except ValueError as exception:
            raise ValueError(f"Invalid compression format '{compression_format}'") from exception


class InitfsCompressionLevel(Enum):
    DEFAULT = "default"
    FAST = "fast"
    BEST = "best"

    @staticmethod
    def from_str(compression_level: str) -> InitfsCompressionLevel:
        try:
            return InitfsCompressionLevel(compression_level)
        except ValueError as exception:
            raise ValueError(f"Invalid compression level '{compression_level}'") from exception


@dataclass
class InitfsCompression:
    format_: InitfsCompressionFormat
    level: InitfsCompressionLevel | None

    @staticmethod
    def from_str(initfs_compression: str) -> InitfsCompression | None:
        segments = initfs_compression.split(":", maxsplit=1)

        try:
            format_ = InitfsCompressionFormat.from_str(segments[0])
        except ValueError:
            # If we can't even figure out the format, the other information is no use.
            return None

        try:
            level = InitfsCompressionLevel.from_str(segments[1]) if len(segments) == 2 else None
        except ValueError:
            level = None

        return InitfsCompression(format_, level)


# FIXME: It feels weird to handle this at parse time.
# we should instead have the Deviceinfo object store
# the attributes for all kernels and require the user
# to specify which one they're using.
# Basically: treat Deviceinfo as a standalone type that
# doesn't need to traverse pmaports.
def _parse_kernel_suffix(info: dict[str, str], device: str, kernel: str | None) -> dict[str, str]:
    """
    Remove the kernel suffix (as selected in 'pmbootstrap init') from
    deviceinfo variables. Related:
    https://wiki.postmarketos.org/wiki/Device_specific_package#Multiple_kernels

    :param info: deviceinfo dict, e.g.:
                 {"a": "first",
                  "b_mainline": "second",
                  "b_downstream": "third"}
    :param device: which device info belongs to
    :param kernel: which kernel suffix to remove (e.g. "mainline")
    :returns: info, but with the configured kernel suffix removed, e.g:
              {"a": "first",
               "b": "second",
               "b_downstream": "third"}
    """
    # We don't support parsing the kernel variants in tests yet, since this code
    # depends on pmaports being available and calls into a whole lot of other code.
    if os.environ.get("PYTEST_CURRENT_TEST", "").startswith("pmb/parse/test_deviceinfo.py"):
        # If you hit this, you're probably trying to add a test for kernel variants.
        # You'll need to figure out how to mock the APKBUILD parsing below.
        assert kernel is None
        return info
    # Do nothing if the configured kernel isn't available in the kernel (e.g.
    # after switching from device with multiple kernels to device with only one
    # kernel)
    kernels = pmb.parse._apkbuild.kernels(device)
    if not kernels or kernel not in kernels:
        logging.verbose(f"parse_kernel_suffix: {kernel} not in {kernels}")
        return info

    ret = copy.copy(info)

    suffix_kernel = kernel.replace("-", "_")
    for key in inspect.get_annotations(Deviceinfo):
        key_kernel = f"{key}_{suffix_kernel}"
        if key_kernel not in ret:
            continue

        # Move ret[key_kernel] to ret[key]
        logging.verbose(f"parse_kernel_suffix: {key_kernel} => {key}")
        ret[key] = ret[key_kernel]
        del ret[key_kernel]

    return ret


@Cache("device", "kernel")
def deviceinfo(device: str | None = None, kernel: str | None = None) -> Deviceinfo:
    """
    :param device: defaults to args.device
    :param kernel: defaults to args.kernel
    """
    context = get_context()
    if not device:
        device = context.config.device
    if not kernel:
        kernel = context.config.kernel

    path = pmb.helpers.devices.find_path(device, "deviceinfo")
    if not path:
        raise NonBugError(
            f"Device '{device}' not found. Run 'pmbootstrap init' to start a new device port or to "
            "choose another device. It may have been renamed, see <https://postmarketos.org/renamed>"
        )

    return Deviceinfo(path, kernel)


class Deviceinfo:
    """
    Variables from deviceinfo. Reference: <https://postmarketos.org/deviceinfo>
    Many of these are unused in pmbootstrap, and still more that are described
    on the wiki are missing. Eventually this class and associated code should
    be moved to a separate library and become the authoritative source of truth
    for the deviceinfo format.
    """

    path: Path
    # general
    format_version: str
    name: str
    manufacturer: str
    codename: str
    year: str
    dtb: str = ""
    arch: Arch

    # device
    chassis: str | None
    keyboard: str | None = ""  # deprecated
    external_storage: str | None = ""
    drm: bool | None = False
    dev_touchscreen: str | None = ""
    dev_touchscreen_calibration: str | None = ""
    append_dtb: str | None = ""

    # bootloader
    flash_method: str = ""
    boot_filesystem: str | None = ""
    create_initfs_extra: bool | None = False
    create_prep_boot: bool | None = False
    initfs_compression: InitfsCompression = InitfsCompression(InitfsCompressionFormat.GZIP, None)

    # flash
    flash_heimdall_partition_kernel: str | None = ""
    flash_heimdall_partition_vendor_boot: str | None = ""
    flash_heimdall_partition_initfs: str | None = ""
    flash_heimdall_partition_rootfs: str | None = ""
    flash_heimdall_partition_system: str | None = ""  # deprecated
    flash_heimdall_partition_vbmeta: str | None = ""
    flash_heimdall_partition_dtbo: str | None = ""
    flash_fastboot_partition_kernel: str | None = ""
    flash_fastboot_partition_vendor_boot: str | None = ""
    flash_fastboot_partition_rootfs: str | None = ""
    flash_fastboot_partition_system: str | None = ""  # deprecated
    flash_fastboot_partition_vbmeta: str | None = ""
    flash_fastboot_partition_dtbo: str | None = ""
    flash_rk_partition_kernel: str | None = ""
    flash_rk_partition_vendor_boot: str | None = ""
    flash_rk_partition_rootfs: str | None = ""
    flash_rk_partition_system: str | None = ""  # deprecated
    flash_mtkclient_partition_kernel: str | None = ""
    flash_mtkclient_partition_vendor_boot: str | None = ""
    flash_mtkclient_partition_rootfs: str | None = ""
    flash_mtkclient_partition_vbmeta: str | None = ""
    flash_mtkclient_partition_dtbo: str | None = ""
    generate_legacy_uboot_initfs: str | None = ""
    kernel_cmdline: str | None = ""
    generate_bootimg: str | None = ""
    header_version: int | None = None
    bootimg_qcdt: str | None = ""
    bootimg_qcdt_type: str | None = ""
    bootimg_mtk_mkimage: str | None = ""  # deprecated
    bootimg_mtk_label_kernel: str | None = ""
    bootimg_mtk_label_ramdisk: str | None = ""
    bootimg_dtb_second: str | None = ""
    bootimg_custom_args: str | None = ""
    flash_offset_base: str | None = ""
    flash_offset_dtb: str | None = ""
    flash_offset_kernel: str | None = ""
    flash_offset_ramdisk: str | None = ""
    flash_offset_second: str | None = ""
    flash_offset_tags: str | None = ""
    flash_pagesize: str | None = ""
    flash_fastboot_max_size: str | None = ""
    flash_sparse: str | None = ""
    flash_sparse_samsung_format: str | None = ""
    rootfs_image_sector_size: str | None = ""
    sd_embed_firmware: str | None = ""
    sd_embed_firmware_step_size: str | None = ""
    partition_blacklist: str | None = ""
    boot_part_start: str | None = ""
    partition_type: str | None = ""
    root_filesystem: str | None = ""
    flash_kernel_on_update: str | None = ""
    cgpt_kpart: str | None = ""
    cgpt_kpart_start: str | None = ""
    cgpt_kpart_size: str | None = ""

    # weston
    weston_pixman_type: str | None = ""

    # keymaps
    keymaps: str | None = ""

    def __init__(self, path: Path, kernel: str | None = None) -> None:
        ret = {}
        with open(path) as handle:
            for line in handle:
                if not line.startswith("deviceinfo_"):
                    continue
                if "=" not in line:
                    raise SyntaxError(f"{path}: No '=' found:\n\t{line}")
                split = line.split("=", 1)
                key = split[0][len("deviceinfo_") :]
                value = split[1].replace('"', "").replace("\n", "")
                ret[key] = value

        ret = _parse_kernel_suffix(ret, ret["codename"], kernel)

        for key, value in ret.items():
            # FIXME: something to turn on and fix in the future
            # if key not in Deviceinfo.__annotations__.keys():
            #     logging.warning(f"deviceinfo: {key} is not a known attribute")
            match key:
                case "arch":
                    setattr(self, key, Arch.from_str(value))
                case "gpu_accelerated":  # deprecated
                    self.drm = value == "true"
                case "header_version":
                    setattr(self, key, int(value))
                case "initfs_compression":
                    setattr(self, key, InitfsCompression.from_str(value))
                case _:
                    setattr(self, key, value)

        if not self.flash_method:
            self.flash_method = "none"
