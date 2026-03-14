# Copyright 2026 Oliver Smith, Paul Adam
# SPDX-License-Identifier: GPL-3.0-or-later
import json
from pathlib import Path

import pmb.parse.apkindex


def apkindex_parse(apkindex_path: Path, package: str | list[str]) -> None:
    result = pmb.parse.apkindex.parse(apkindex_path)
    if package:
        if package not in result:
            raise RuntimeError(f"Package not found in the APKINDEX: {package}")
        if isinstance(package, list):
            raise AssertionError
        result_temp = result[package]
        if isinstance(result_temp, pmb.parse.apkindex.ApkindexBlock):
            raise AssertionError
        result = result_temp
    print(json.dumps(result, indent=4))
