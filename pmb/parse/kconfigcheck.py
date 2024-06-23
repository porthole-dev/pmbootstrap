# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import os
import logging

import pmb.config
from pmb.core.pkgrepo import pkgrepo_default_path
from pmb.helpers.toml import load_toml_file
from pmb.meta import Cache
from pathlib import Path


@Cache()
def get_path() -> Path:
    """Get the kconfigcheck.toml from current pmaports branch if it exists, or
    as fallback the v24.06 version shipped with pmbootstrap.
    """
    ret: Path
    ret = Path(pkgrepo_default_path(), "kconfigcheck.toml")
    if os.path.exists(ret):
        return ret

    logging.info(
        "NOTE: couldn't find kconfigcheck.toml in pmaports dir, using"
        " the version from postmarketOS v24.06"
    )
    return Path(pmb.config.pmb_src, "pmb/data/kconfigcheck.toml")


def sanity_check(toml: dict) -> None:
    """Ensure the kconfigcheck.toml file has the expected structure."""
    path = get_path()

    if "aliases" not in toml:
        raise RuntimeError(f"{path}: missing [aliases] section")

    for alias in toml["aliases"].keys():
        for category in toml["aliases"][alias]:
            if not category.startswith("category:"):
                raise RuntimeError(
                    f"{path}: alias {alias}: all categories must start with 'category:'!"
                )

    for section in toml.keys():
        if section == "aliases":
            continue
        if not section.startswith("category:"):
            raise RuntimeError(f"{path}: unexpected section: {section}")


@Cache("name")
def read_category(name: str) -> dict[str, dict]:
    """Read either one category or one alias (for one or more categories) from
    kconfigcheck.toml.
    """
    toml = load_toml_file(get_path())
    sanity_check(toml)

    # Potentially resolve category alias
    categories = [name]
    if name in toml["aliases"]:
        categories = []
        for category in toml["aliases"][name]:
            categories += [category.split(":", 1)[1]]
        logging.debug(f"kconfigcheck: read_component: '{name}' -> {categories}")

    ret = {}
    for category in categories:
        key = f"category:{category}"
        if key not in toml:
            raise RuntimeError(f"{get_path()}: couldn't find {key}")
        ret[key] = toml[key]

    return ret
