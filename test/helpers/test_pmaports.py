# Copyright 2025 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later

from pmb.helpers.pmaports import check_version_constraints


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
