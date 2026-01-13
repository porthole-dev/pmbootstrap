# Copyright 2024 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import os
from pathlib import Path

import pmb.config
from pmb.core.arch import Arch
from pmb.core.pkgrepo import pkgrepo_default_path
from pmb.helpers.toml import load_toml_file
from pmb.meta import Cache


@Cache()
def get_path() -> Path:
    """
    Get the kconfigcheck.toml from current pmaports branch if it exists, or
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

    for alias in toml["aliases"]:
        for category in toml["aliases"][alias]:
            if not category.startswith("category:"):
                raise RuntimeError(
                    f"{path}: alias {alias}: all categories must start with 'category:'!"
                )

    for section in toml:
        if section == "aliases":
            continue
        if not all(cat.startswith("category:") for cat in section.split()):
            raise RuntimeError(f"{path}: unexpected section: {section}")
        for versions in toml[section]:
            for arches in toml[section][versions]:
                if arches == "all":
                    continue
                if not isinstance(toml[section][versions][arches], dict):
                    raise RuntimeError(f"{path}: {section} is missing architecture information")
                for arch in arches.split(" "):
                    _ = Arch.from_str(arch)


@Cache("categories")
def read_categories(categories: list[str]) -> dict[str, dict]:
    """Read multiple categories (including aliases) from kconfigcheck.toml."""
    toml = load_toml_file(get_path())
    sanity_check(toml)

    # Potentially resolve category alias
    # category: exists
    real_categories: dict[str, bool] = {}
    for category in categories:
        if category in toml["aliases"]:
            resolved_aliases = [c.split(":", 1)[1] for c in toml["aliases"][category]]
            real_categories |= dict.fromkeys(resolved_aliases, False)
            logging.debug(f"kconfigcheck: read_categories: '{category}' -> {resolved_aliases}")
        else:
            real_categories[category] = False

    ret = {}

    for key in toml:
        # Keys may contain multiple space-separated category:name entries, which all need
        # to be satisfied for a section to be considered.
        if key.startswith("category:"):
            # This must be a kconfigcheck section
            required_categories = [c.split(":", 1)[1] for c in key.split()]
            all_requirements_met = True

            for required_category in required_categories:
                if required_category in real_categories:
                    # This category exists!
                    real_categories[required_category] = True
                else:
                    # We still keep going through categories since we still want
                    # to be able to error on nonexisting categories
                    all_requirements_met = False

            if all_requirements_met:
                logging.debug(f"kconfigcheck: section {key} has all requirements met")
                ret[key] = toml[key]

    # Make sure that all specified categories actually exist in the TOML
    for category, exists in real_categories.items():
        if not exists:
            raise RuntimeError(f"{get_path()}: couldn't find {category}")

    return ret
