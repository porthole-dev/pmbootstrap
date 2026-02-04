# Copyright 2026 Pablo Correa Gomez
# SPDX-License-Identifier: GPL-3.0-or-later

from pmb.helpers.package import remove_operators

def test_remove_operators() -> None:
    assert remove_operators("soc-qcom") == "soc-qcom"
    assert remove_operators("soc-qcom>=0.34") == "soc-qcom"
    assert remove_operators("soc-qcom~1.3") == "soc-qcom"
    assert remove_operators("!soc-qcom") == "!soc-qcom"
