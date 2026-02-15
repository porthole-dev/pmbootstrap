# Copyright 2025 Oliver Smith
# Copyright 2026 Pablo Correa Gomez
# SPDX-License-Identifier: GPL-3.0-or-later

from pmb.helpers.package import check_version_constraints, remove_operators


def test_remove_operators() -> None:
    assert remove_operators("soc-qcom") == "soc-qcom"
    assert remove_operators("soc-qcom>=0.34") == "soc-qcom"
    assert remove_operators("soc-qcom~1.3") == "soc-qcom"
    assert remove_operators("!soc-qcom") == "!soc-qcom"


def test_check_version_constraints() -> None:
    assert check_version_constraints("hello-world>=1.1", "1.0") is False
    assert check_version_constraints("hello-world>=1.0", "1.0") is True
    assert check_version_constraints("hello-world>=0.9", "1.0") is True

    assert check_version_constraints("hello-world>1.1", "1.0") is False
    assert check_version_constraints("hello-world>1.0", "1.0") is False
    assert check_version_constraints("hello-world>0.9", "1.0") is True

    assert check_version_constraints("hello-world<=1.1", "1.0") is True
    assert check_version_constraints("hello-world<=1.0", "1.0") is True
    assert check_version_constraints("hello-world<=0.9", "1.0") is False

    assert check_version_constraints("hello-world<1.1", "1.0") is True
    assert check_version_constraints("hello-world<1.0", "1.0") is False
    assert check_version_constraints("hello-world<0.9", "1.0") is False

    # Unexpected operator must always return True. We don't handle "=" and
    # operators with "~" (fuzzy matching) yet, so keep the existing behavior
    # for those and just install the pmaports package if there is one in that
    # case. This can be added later if we have a practical use case for it.
    assert check_version_constraints("hello-world♻️1.1", "1.0") is True
    assert check_version_constraints("hello-world♻️1.0", "1.0") is True
    assert check_version_constraints("hello-world♻️0.9", "1.0") is True
