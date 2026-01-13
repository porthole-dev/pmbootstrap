# Copyright 2025 Pablo Correa Gomez
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from pmb.parse.kconfigcheck import sanity_check


def test_basic(pmb_args: None) -> None:
    toml = {
        "aliases": {"community": ["category:default"]},
        "category:default": {">=0.0.0": {"all": {"CGROUPS": "y"}}},
    }
    sanity_check(toml)


def test_no_aliases() -> None:
    toml = {
        "category:default": {">=0.0.0": {"all": {"CGROUPS": "y"}}},
    }
    with pytest.raises(RuntimeError) as no_aliases:
        sanity_check(toml)
    assert "missing [aliases] section" in str(no_aliases.value)


def test_missing_category() -> None:
    toml = {
        "aliases": {"community": ["default"]},
        "default": {">=0.0.0": {"all": {"CGROUPS": "y"}}},
    }
    with pytest.raises(RuntimeError) as missing_category:
        sanity_check(toml)
    assert "all categories must start with 'category:'!" in str(missing_category.value)


def test_bad_arch() -> None:
    toml = {
        "aliases": {"community": ["category:default"]},
        "category:default": {">=0.0.0": {"x86 x64_64": {"CGROUPS": "y"}}},
    }
    with pytest.raises(ValueError) as bad_arch:
        sanity_check(toml)
    assert "Invalid architecture: 'x64_64'" in str(bad_arch.value)


def test_missing_arch() -> None:
    toml = {
        "aliases": {"community": ["category:default"]},
        "category:default": {">=0.0.0": {"all": {"NET": "y"}}},
        "category:containers": {">=0.0.0": {"CGROUPS": "y"}},
    }
    with pytest.raises(RuntimeError) as missing_arch:
        sanity_check(toml)
    assert "category:containers is missing architecture information" in str(missing_arch.value)


def test_multiple_categories(pmb_args: None) -> None:
    toml = {
        "aliases": {"community": ["category:default"]},
        "category:default category:uefi": {">=0.0.0": {"all": {"CGROUPS": "y"}}},
    }
    sanity_check(toml)


def test_multiple_categories_missing_category(pmb_args: None) -> None:
    toml = {
        "aliases": {"community": ["category:default"]},
        "category:default uefi": {">=0.0.0": {"all": {"CGROUPS": "y"}}},
    }
    with pytest.raises(RuntimeError) as missing_category:
        sanity_check(toml)
    assert "unexpected section: category:default uefi" in str(missing_category.value)
