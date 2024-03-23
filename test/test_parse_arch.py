# Copyright 2024 Stefan "Newbyte" Hansson
# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

import pmb.parse.arch


def test_machine_type_to_alpine() -> None:
    fake_machine_type = "not-a-machine-type"

    with pytest.raises(ValueError) as e:
        pmb.parse.arch.machine_type_to_alpine(fake_machine_type)
        assert e == f"Can not map machine type {fake_machine_type} to the right Alpine Linux architecture"

    assert pmb.parse.arch.machine_type_to_alpine("armv7l") == "armv7"
