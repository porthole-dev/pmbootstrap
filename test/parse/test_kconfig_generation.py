# Copyright 2025 Clayton Craft
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
from _pytest.monkeypatch import MonkeyPatch

import pmb.parse.kconfigcheck
from pmb.core.arch import Arch
from pmb.parse.kconfig import create_fragment
from pmb.types import Apkbuild


@pytest.fixture
def mock_kconfigcheck(monkeypatch: MonkeyPatch) -> None:
    """Mock kconfigcheck.read_category to return test rules."""

    def mock_read_category(category: str) -> dict:
        if category == "default":
            return {
                "category:default": {
                    ">=0": {
                        "all": {
                            "BASE": "y",
                            "DEBUG": "n",
                            "CRYPTO_MODULES": ["aes", "sha256", "cbc"],
                        }
                    }
                }
            }
        elif category == "community":
            return {
                "category:community": {
                    ">=6.0": {
                        "aarch64": {
                            "DRM": "m",
                            "CMDLINE": "console=tty0",
                        }
                    }
                }
            }
        return {}

    monkeypatch.setattr(pmb.parse.kconfigcheck, "read_category", mock_read_category)


def test_create_fragment_basic(mock_kconfigcheck: None) -> None:
    """Test fragment generation from kconfigcheck rules."""
    apkbuild: Apkbuild = {
        "pkgver": "6.6.0",
        "options": ["pmb:kconfigcheck-community"],
    }

    fragment = create_fragment(apkbuild, Arch.aarch64)

    # Check default category included
    assert "CONFIG_BASE=y" in fragment
    assert "# CONFIG_DEBUG is not set" in fragment
    assert 'CONFIG_CRYPTO_MODULES="aes,sha256,cbc"' in fragment

    # Check community category included
    assert "CONFIG_DRM=m" in fragment
    assert 'CONFIG_CMDLINE="console=tty0"' in fragment


def test_create_fragment_version_filtering(mock_kconfigcheck: None) -> None:
    """Test that version constraints are respected."""
    apkbuild: Apkbuild = {
        "pkgver": "5.15.0",  # Below 6.0
        "options": ["pmb:kconfigcheck-community"],
    }

    fragment = create_fragment(apkbuild, Arch.aarch64)

    # Default should be included
    assert "CONFIG_BASE=y" in fragment

    # Community (>=6.0) should NOT be included
    assert "CONFIG_DRM" not in fragment


def test_create_fragment_arch_filtering(mock_kconfigcheck: None) -> None:
    """Test that arch constraints are respected."""
    apkbuild: Apkbuild = {
        "pkgver": "6.6.0",
        "options": ["pmb:kconfigcheck-community"],
    }

    fragment = create_fragment(apkbuild, Arch.x86_64)

    # Default (all arches) should be included
    assert "CONFIG_BASE=y" in fragment

    # Community (aarch64 only) should NOT be included
    assert "CONFIG_DRM" not in fragment
