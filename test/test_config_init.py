"""
Copyright 2019 Oliver Smith

This file is part of pmbootstrap.

pmbootstrap is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pmbootstrap is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pmbootstrap.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
import pytest
import sys

# Import from parent directory
sys.path.insert(0, os.path.realpath(
    os.path.join(os.path.dirname(__file__) + "/..")))
import pmb.config.init


def test_require_programs(monkeypatch):
    func = pmb.config.init.require_programs

    # Nothing missing
    func()

    # Missing program
    invalid = "invalid-program-name-here-asdf"
    monkeypatch.setattr(pmb.config, "required_programs", [invalid])
    with pytest.raises(RuntimeError) as e:
        func()
    assert str(e.value).startswith("Can't find all programs")
