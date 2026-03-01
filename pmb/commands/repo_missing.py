# Copyright 2023 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import json

import pmb.helpers.repo_missing
from pmb.core.arch import Arch
from pmb.helpers import logging


def repo_missing(arch: Arch | None, built: bool) -> None:
    if arch is None:
        raise AssertionError
    if built:
        logging.warning(
            "WARNING: --built is deprecated (bpo#148: this warning is expected on build.postmarketos.org for now)"
        )
    missing = pmb.helpers.repo_missing.generate(arch)
    print(json.dumps(missing, indent=4))
