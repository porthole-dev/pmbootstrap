#!/usr/bin/env python3
# Copyright 2026 Giuseppe Maggio
# SPDX-License-Identifier: GPL-3.0-or-later
r"""
Compare pmbootstrap's APKBUILD parser with what the shell computes.

Every APKBUILD is sourced with busybox sh for several architectures, the way
abuild does it, and the attributes pmbootstrap cares about are compared with
pmb.parse.apkbuild(arch=...). With --baseline, the same is done with another
pmbootstrap source tree (e.g. an upstream checkout, which gets no arch), and
the report lists what got fixed and what regressed.

This RUNS the top-level code of every APKBUILD: use a container.

    find aports pmaports -name APKBUILD | xargs \
        helpers/apkbuild-vs-shell.py --baseline /tmp/pmbootstrap-upstream
"""

import argparse
import inspect
import json
import subprocess
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

ARCHES = ["aarch64", "x86_64", "armv7", "armhf", "riscv64", "x86", "loongarch64", "ppc64le"]
ATTRS = [
    "depends",
    "makedepends",
    "makedepends_build",
    "makedepends_host",
    "checkdepends",
    "depends_dev",
    "options",
    "provides",
    "arch",
    "install",
    "triggers",
]
PRELUDE = """
arch_to_hostspec() {
    case "$1" in
    armhf) echo armv6-alpine-linux-musleabihf ;;
    armv7) echo armv7-alpine-linux-musleabihf ;;
    x86) echo i586-alpine-linux-musl ;;
    *) echo "$1-alpine-linux-musl" ;;
    esac
}
arch_to_triplet() { arch_to_hostspec "$@"; }
"""
Result = dict[str, dict[str, Any]]


def shell(path: str) -> Result:
    script = PRELUDE
    values = " ".join(f'"${attr}"' for attr in [*ATTRS, "subpackages"])
    for arch in ARCHES:
        script += f"""(
            CARCH={arch}; CTARGET_ARCH={arch}; CBUILD=$(arch_to_hostspec {arch})
            CHOST=$CBUILD; CTARGET=$CBUILD; startdir=$PWD; srcdir=$PWD/src; pkgdir=$PWD/pkg
            . ./APKBUILD >/dev/null 2>&1 </dev/null
            printf '%s\\036' {values}; printf '\\035'
        )
        """
    out = subprocess.run(
        ["timeout", "10", "sh", "-c", script],
        cwd=Path(path).parent,
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    ).stdout
    ret: Result = {}
    for arch, block in zip(ARCHES, out.split("\035"), strict=False):
        fields = block.split("\036")
        if len(fields) > len(ATTRS):
            ret[arch] = {attr: sorted(set(fields[i].split())) for i, attr in enumerate(ATTRS)}
            ret[arch]["subpackages"] = sorted({s.split(":")[0] for s in fields[len(ATTRS)].split()})
    return ret


def parse(src: str, path: str) -> Result:
    sys.path.insert(0, src)
    import pmb.helpers.logging
    import pmb.parse._apkbuild
    from pmb.core.arch import Arch

    pmb.helpers.logging.add_verbose_log_level()
    parser = pmb.parse._apkbuild._apkbuild_from_lines
    aware = "arch" in inspect.signature(parser).parameters
    ret: Result = {}
    for arch in ARCHES:
        kwargs = {"arch": Arch.from_str(arch)} if aware else {}
        try:
            apkbuild = parser(
                pmb.parse._apkbuild.read_file(Path(path)), Path(path), False, False, **kwargs
            )
        except Exception as exception:
            ret[arch] = {"error": type(exception).__name__}
            continue
        ret[arch] = {attr: sorted(set(apkbuild[attr])) for attr in ATTRS}
        ret[arch]["subpackages"] = sorted(apkbuild["subpackages"])
    return ret


def parse_all(src: str, paths: list[str]) -> list[Result]:
    """Parse in a child process per tree, so two pmb packages never mix."""
    cmd = [sys.executable, __file__, "--parse-with", src, *paths]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)


def chunks(paths: list[str], size: int = 200) -> list[list[str]]:
    return [paths[i : i + size] for i in range(0, len(paths), size)]


def main() -> None:
    argparser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    argparser.add_argument("--baseline", help="another pmbootstrap source tree to compare with")
    argparser.add_argument("--parse-with", help=argparse.SUPPRESS)
    argparser.add_argument("apkbuilds", nargs="+")
    args = argparser.parse_args()
    if args.parse_with:
        print(json.dumps([parse(args.parse_with, path) for path in args.apkbuilds]))
        return
    here = str(Path(__file__).resolve().parent.parent)

    with ProcessPoolExecutor() as executor:
        truths = list(executor.map(shell, args.apkbuilds, chunksize=8))
        groups = chunks(args.apkbuilds)
        new = [r for rs in executor.map(parse_all, [here] * len(groups), groups) for r in rs]
        old = new
        if args.baseline:
            base = [args.baseline] * len(groups)
            old = [r for rs in executor.map(parse_all, base, groups) for r in rs]

    counts: Counter[str] = Counter()
    for path, truth, before, after in zip(args.apkbuilds, truths, old, new, strict=True):
        for arch, expected in truth.items():
            if "error" in after[arch] and "error" not in before[arch]:
                print(f"NEW ERROR {path} {arch}: {after[arch]['error']}")
                counts["new errors"] += 1
                continue
            for attr, value in expected.items():
                right_before = before[arch].get(attr) == value
                right_after = after[arch].get(attr) == value
                if right_before and not right_after:
                    print(f"REGRESSION {path} {arch} {attr}: {after[arch].get(attr)} != {value}")
                    counts["regressions"] += 1
                elif right_after:
                    counts["fixed" if not right_before else "right"] += 1
                else:
                    counts["wrong"] += 1
    print(json.dumps(counts))
    sys.exit(1 if counts["regressions"] or counts["new errors"] else 0)


if __name__ == "__main__":
    main()
