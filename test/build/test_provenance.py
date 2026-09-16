# Copyright 2026 Giuseppe Maggio
# SPDX-License-Identifier: GPL-3.0-or-later
import subprocess
import tempfile
from pathlib import Path

from pmb.build.backend import git_provenance


def _git(repo: Path, *args: str) -> str:
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
        "GIT_COMMITTER_DATE": "@1700000000 +0000",
        "GIT_AUTHOR_DATE": "@1700000000 +0000",
        "PATH": "/usr/bin:/bin",
    }
    return subprocess.run(
        ["git", "-C", repo, *args], env=env, check=True, capture_output=True, text=True
    ).stdout.strip()


def test_git_provenance(pmb_args: None, tmp_path: Path) -> None:
    repo = tmp_path / "pmaports"
    aport = repo / "main/hello"
    other = repo / "main/other"
    aport.mkdir(parents=True)
    other.mkdir(parents=True)
    _git(repo, "init", "-q")
    (aport / "APKBUILD").write_text("pkgname=hello\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "hello")
    commit = _git(repo, "rev-parse", "HEAD")

    # The last commit that touched the aport, not HEAD
    (other / "APKBUILD").write_text("pkgname=other\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "other")
    assert git_provenance(aport) == {
        "ABUILD_LAST_COMMIT": commit,
        "SOURCE_DATE_EPOCH": "1700000000",
    }

    # Uncommitted changes: abuild's "-dirty", and no date from git
    (aport / "APKBUILD").write_text("pkgname=hello\npkgrel=1\n")
    assert git_provenance(aport) == {"ABUILD_LAST_COMMIT": f"{commit}-dirty"}

    # A new aport that was never committed
    new = repo / "main/new"
    new.mkdir()
    (new / "APKBUILD").write_text("pkgname=new\n")
    assert git_provenance(new) == {"ABUILD_LAST_COMMIT": "-dirty"}


def test_git_provenance_outside_git(pmb_args: None) -> None:
    # Not tmp_path: pytest puts that inside this git checkout, and an aport
    # there is in a checkout, just not its own.
    with tempfile.TemporaryDirectory(dir="/tmp") as outside:
        (Path(outside) / "APKBUILD").write_text("pkgname=hello\n")
        assert git_provenance(Path(outside)) == {}
