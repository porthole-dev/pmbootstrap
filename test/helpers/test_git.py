# Copyright 2025 Stefan Hansson
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

from pmb.helpers.git import _is_path_hidden, remote_to_name_and_clean_url


def test_remote_to_clean_url() -> None:
    name_1 = "origin"
    name_2 = "newbyte"

    raw_http_remote = "origin	https://gitlab.postmarketos.org/postmarketOS/pmaports.git (fetch)"
    clean_http_remote = "https://gitlab.postmarketos.org/postmarketOS/pmaports.git (fetch)"

    assert remote_to_name_and_clean_url(raw_http_remote) == (name_1, clean_http_remote)

    raw_http_remote_with_token = "origin	https://gitlab-ci-token:QVy1PB7sTxfy4pqfZM1U@gitlab.postmarketos.org/postmarketOS/pmaports.git (fetch)"

    assert remote_to_name_and_clean_url(raw_http_remote_with_token) == (name_1, clean_http_remote)

    raw_git_remote = "newbyte	git@gitlab.postmarketos.org:postmarketOS/pmaports.git (fetch)"
    clean_git_remote = "git@gitlab.postmarketos.org:postmarketOS/pmaports.git (fetch)"

    assert remote_to_name_and_clean_url(raw_git_remote) == (name_2, clean_git_remote)


def test_is_path_hidden() -> None:
    assert _is_path_hidden(Path(".ci/coolfile.txt"))
    assert _is_path_hidden(Path(".well-known/funding-manifest-urls"))
    assert _is_path_hidden(Path(".some-new-folder/with/really/deep/nesting/yeah.txt"))
    assert _is_path_hidden(Path(".shellcheckrc"))
    assert _is_path_hidden(Path("device/.shared-patches/something.patch"))

    assert not _is_path_hidden(Path("device/community/device-samsung-m0/APKBUILD"))
    assert not _is_path_hidden(Path("main/hello-world/main.c"))
    assert not _is_path_hidden(Path("temp/akms/akms.trigger"))
    assert not _is_path_hidden(Path("docs/Makefile"))
    assert not _is_path_hidden(Path("extra-repos/systemd/systemd/wired.network"))
