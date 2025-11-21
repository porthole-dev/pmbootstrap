# Copyright 2025 Stefan Hansson
# SPDX-License-Identifier: GPL-3.0-or-later

from pmb.helpers.git import remote_to_name_and_clean_url


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
