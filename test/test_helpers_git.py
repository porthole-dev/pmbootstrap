"""
Copyright 2020 Oliver Smith

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
import sys
import pytest
import shutil

# Import from parent directory
sys.path.insert(0, os.path.realpath(
    os.path.join(os.path.dirname(__file__) + "/..")))
import pmb.helpers.git
import pmb.helpers.logging
import pmb.helpers.run


@pytest.fixture
def args(request):
    import pmb.parse
    sys.argv = ["pmbootstrap", "init"]
    args = pmb.parse.arguments()
    args.log = args.work + "/log_testsuite.txt"
    pmb.helpers.logging.init(args)
    request.addfinalizer(args.logfd.close)
    return args


def test_get_path(args):
    func = pmb.helpers.git.get_path
    args.work = "/wrk"
    args.aports = "/tmp/pmaports"

    assert func(args, "aports_upstream") == "/wrk/cache_git/aports_upstream"
    assert func(args, "pmaports") == "/tmp/pmaports"


def test_can_fast_forward(args, tmpdir):
    tmpdir = str(tmpdir)
    func = pmb.helpers.git.can_fast_forward
    branch_origin = "fake-branch-origin"

    def run_git(git_args):
        pmb.helpers.run.user(args, ["git"] + git_args, tmpdir, "stdout")

    # Create test git repo
    run_git(["init", "."])
    run_git(["commit", "--allow-empty", "-m", "commit on master"])
    run_git(["checkout", "-b", branch_origin])
    run_git(["commit", "--allow-empty", "-m", "commit on branch_origin"])
    run_git(["checkout", "master"])

    # Can fast-forward
    assert func(args, tmpdir, branch_origin) is True

    # Can't fast-forward
    run_git(["commit", "--allow-empty", "-m", "commit on master #2"])
    assert func(args, tmpdir, branch_origin) is False

    # Git command fails
    with pytest.raises(RuntimeError) as e:
        func(args, tmpdir, "invalid-branch")
    assert str(e.value).startswith("Unexpected exit code")


def test_clean_worktree(args, tmpdir):
    tmpdir = str(tmpdir)
    func = pmb.helpers.git.clean_worktree

    def run_git(git_args):
        pmb.helpers.run.user(args, ["git"] + git_args, tmpdir, "stdout")

    # Create test git repo
    run_git(["init", "."])
    run_git(["commit", "--allow-empty", "-m", "commit on master"])

    assert func(args, tmpdir) is True
    pmb.helpers.run.user(args, ["touch", "test"], tmpdir)
    assert func(args, tmpdir) is False


def test_get_upstream_remote(args, monkeypatch, tmpdir):
    tmpdir = str(tmpdir)
    func = pmb.helpers.git.get_upstream_remote
    name_repo = "test"

    # Override get_path()
    def get_path(args, name_repo):
        return tmpdir
    monkeypatch.setattr(pmb.helpers.git, "get_path", get_path)

    # Override pmb.config.git_repos
    url = "https://postmarketos.org/get-upstream-remote-test.git"
    git_repos = {"test": url}
    monkeypatch.setattr(pmb.config, "git_repos", git_repos)

    def run_git(git_args):
        pmb.helpers.run.user(args, ["git"] + git_args, tmpdir, "stdout")

    # Create git repo
    run_git(["init", "."])
    run_git(["commit", "--allow-empty", "-m", "commit on master"])

    # No upstream remote
    with pytest.raises(RuntimeError) as e:
        func(args, name_repo)
    assert "could not find remote name for URL" in str(e.value)

    run_git(["remote", "add", "hello", url])
    assert func(args, name_repo) == "hello"


def test_pull_non_existing(args):
    assert pmb.helpers.git.pull(args, "non-existing-repo-name") == 1


def test_pull(args, monkeypatch, tmpdir):
    """ Test pmb.helpers.git.pull """
    # --- PREPARATION: git repos ---
    # Prepare three git repos:
    # * local: like local clone of pmaports.git
    # * remote: emulate a remote repository, that we can add to "local", so we
    #           can pass the tracking-remote tests in pmb.helpers.git.pull
    # * remote2: unexpected remote, that pmbootstrap can complain about
    path_local = str(tmpdir) + "/local"
    path_remote = str(tmpdir) + "/remote"
    path_remote2 = str(tmpdir) + "/remote2"
    os.makedirs(path_local)
    os.makedirs(path_remote)
    os.makedirs(path_remote2)

    def run_git(git_args, path=path_local):
        pmb.helpers.run.user(args, ["git"] + git_args, path, "stdout")

    # Remote repos
    run_git(["init", "."], path_remote)
    run_git(["commit", "--allow-empty", "-m", "commit: remote"], path_remote)
    run_git(["init", "."], path_remote2)
    run_git(["commit", "--allow-empty", "-m", "commit: remote2"], path_remote2)

    # Local repo (with master -> origin2/master)
    run_git(["init", "."])
    run_git(["remote", "add", "-f", "origin", path_remote])
    run_git(["remote", "add", "-f", "origin2", path_remote2])
    run_git(["checkout", "-b", "master", "--track", "origin2/master"])

    # --- PREPARATION: function overrides ---
    # get_path()
    def get_path(args, name_repo):
        return path_local
    monkeypatch.setattr(pmb.helpers.git, "get_path", get_path)

    # get_upstream_remote()
    def get_u_r(args, name_repo):
        return "origin"
    monkeypatch.setattr(pmb.helpers.git, "get_upstream_remote", get_u_r)

    # --- TEST RETURN VALUES ---
    # Not on official branch
    func = pmb.helpers.git.pull
    name_repo = "test"
    run_git(["checkout", "-b", "inofficial-branch"])
    assert func(args, name_repo) == -1

    # Workdir is not clean
    run_git(["checkout", "master"])
    shutil.copy(__file__, path_local + "/test.py")
    assert func(args, name_repo) == -2
    os.unlink(path_local + "/test.py")

    # Tracking different remote
    assert func(args, name_repo) == -3

    # Let master track origin/master
    run_git(["checkout", "-b", "temp"])
    run_git(["branch", "-D", "master"])
    run_git(["checkout", "-b", "master", "--track", "origin/master"])

    # Already up to date
    assert func(args, name_repo) == 2

    # Can't fast-forward
    run_git(["commit", "--allow-empty", "-m", "test"])
    assert func(args, name_repo) == -4

    # Fast-forward successfully
    run_git(["reset", "--hard", "origin/master"])
    run_git(["commit", "--allow-empty", "-m", "new"], path_remote)
    assert func(args, name_repo) == 0
