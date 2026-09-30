# Copyright 2026 Giuseppe Maggio
# SPDX-License-Identifier: GPL-3.0-or-later
"""Private container /dev: create only selected image partitions from sysfs."""

import ast
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace


def test_missing_image_partition_node() -> None:
    source = (Path(__file__).parents[1] / "pmb/install/partition.py").read_text()
    tree = ast.parse(source)
    node = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.If) and ast.unparse(n.test) == "image_disk and (not source.exists())"
    )
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        partition = root / "loop0p2"
        sysdev = root / "sys" / partition.name / "dev"
        sysdev.parent.mkdir(parents=True)
        sysdev.write_text("259:2\n")
        calls: list[list[object]] = []
        scope = {
            "source": partition,
            "image_disk": False,
            "Path": lambda _: root / "sys",
            "pmb": SimpleNamespace(
                helpers=SimpleNamespace(
                    run=SimpleNamespace(root=lambda command: calls.append(command))
                )
            ),
        }
        code = compile(ast.Module(body=[node], type_ignores=[]), "partition.py", "exec")
        exec(code, scope)  # ruff:ignore[exec-builtin] - execute actual checked-out branch with mocked privilege
        assert not calls  # physical disk installation must not create host nodes
        scope["image_disk"] = True
        exec(code, scope)  # ruff:ignore[exec-builtin]
        assert calls == [["mknod", partition, "b", "259", "2"]]
        partition.touch()
        exec(code, scope)  # ruff:ignore[exec-builtin]
        assert len(calls) == 1  # an existing node is never replaced
