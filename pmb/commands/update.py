# Copyright 2026 Hugo Posnic
# SPDX-License-Identifier: GPL-3.0-or-later
import pmb.helpers.repo
from pmb.core.arch import Arch
from pmb.helpers import logging


def update(arch: Arch | None, non_existing: str) -> None:
    existing_only = not non_existing
    if not pmb.helpers.repo.update(arch, True, existing_only):
        logging.info(
            "No APKINDEX files exist, so none have been updated."
            " The pmbootstrap command downloads the APKINDEX files on"
            " demand."
        )
        logging.info(
            "If you want to force downloading the APKINDEX files for"
            " all architectures (not recommended), use:"
            " pmbootstrap update --non-existing"
        )
