# Copyright 2024 Caleb Connolly
# SPDX-License-Identifier: GPL-3.0-or-later

import shutil
import tempfile
from pathlib import Path

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.monkeypatch import MonkeyPatch
from _pytest.tmpdir import TempPathFactory

import pmb.core
from pmb.core.arch import Arch
from pmb.core.context import Context, get_context
from pmb.helpers.args import init as init_args
from pmb.types import PmbArgs

_testdir = Path(__file__).parent / "data/tests"


# request can be specified using parameterize from test cases
# e.g. @pytest.mark.parametrize("config_file", ["no-repos"], indirect=True)
# will set request.param to "no-repos"
@pytest.fixture
def config_file(tmp_path_factory: TempPathFactory, request: FixtureRequest) -> Path:
    """Fixture to create a temporary pmbootstrap_v3.cfg file."""
    tmp_path = tmp_path_factory.mktemp("pmbootstrap")

    flavour = "default"
    if hasattr(request, "param") and request.param:
        flavour = request.param

    out_file = tmp_path / "pmbootstrap_v3.cfg"
    workdir = tmp_path / "work"
    workdir.mkdir()

    configs = {"default": f"aports = {workdir / 'cache_git' / 'pmaports'}", "no-repos": "aports = "}

    file = _testdir / "pmbootstrap_v3.cfg"
    print(f"CONFIG: {out_file}")
    cfg = configs[flavour]
    contents = file.read_text().format(workdir, cfg)

    out_file.write_text(contents)
    return out_file


@pytest.fixture
def device_package(config_file: Path) -> Path:
    """Fixture to create a temporary deviceinfo file."""
    mock_device = "qemu-amd64"
    pkgdir = config_file.parent / f"device-{mock_device}"
    pkgdir.mkdir()

    for file in ["APKBUILD", "deviceinfo"]:
        shutil.copy(_testdir / f"{file}.{mock_device}", pkgdir / file)

    return pkgdir


@pytest.fixture(autouse=True)
def find_required_programs() -> None:
    """Fixture to find required programs for pmbootstrap."""

    pmb.config.require_programs()


@pytest.fixture
def mock_devices_find_path(device_package: Path, monkeypatch: MonkeyPatch) -> None:
    """Fixture to mock pmb.helpers.devices.find_path()"""

    def mock_find_path(codename: str, file: str = "") -> Path | None:
        print(f"mock_find_path({codename}, {file})")
        out = device_package / file
        if not out.exists():
            return None

        return out

    monkeypatch.setattr("pmb.helpers.devices.find_path", mock_find_path)


@pytest.fixture(autouse=True)
def logfile(tmp_path_factory: TempPathFactory) -> Path:
    """Setup logging for all tests."""
    from pmb.helpers import logging

    tmp_path = tmp_path_factory.getbasetemp()
    logfile = tmp_path / "log_testsuite.txt"
    logging.init(logfile, verbose=True)

    return logfile


@pytest.fixture(autouse=True)
def setup_mock_ask(monkeypatch: MonkeyPatch) -> None:
    """Common setup to mock cli.ask() to avoid reading from stdin"""
    import pmb.helpers.cli

    def mock_ask(
        question: str = "Continue?",
        choices: list[str] = ["y", "n"],
        default: str = "n",
        lowercase_answer: bool = True,
        validation_regex: None = None,
        complete: None = None,
    ) -> str:
        return default

    monkeypatch.setattr(pmb.helpers.cli, "ask", mock_ask)


# FIXME: get/set_context() is a bad hack :(
@pytest.fixture
def mock_context(monkeypatch: MonkeyPatch) -> None:
    """Mock set_context() to bypass sanity checks. Ideally we would
    mock get_context() as well, but since every submodule of pmb imports
    it like "from pmb.core.context import get_context()", we can't
    actually override it with monkeypatch.setattr(). So this is the
    best we can do... set_context() is only called from one place and is
    done so with the full namespace, so this works."""

    def mock_set_context(ctx: Context) -> None:
        print(f"mock_set_context({ctx})")
        setattr(pmb.core.context, "__context", ctx)

    monkeypatch.setattr("pmb.core.context.set_context", mock_set_context)


# FIXME: get_context() at runtime somehow doesn't return the
# custom context we set up here.
@pytest.fixture
def pmb_args(config_file: Path, mock_context: None, logfile: Path) -> None:
    """This is (still) a hack, since a bunch of the codebase still
    expects some global state to be initialised. We do that here."""

    args = PmbArgs()
    args.config = config_file
    args.aports = None
    args.timeout = 900
    args.details_to_stdout = False
    args.quiet = False
    args.verbose = True
    args.offline = False
    args.action = "init"
    args.cross = False
    args.ccache = True
    args.log = logfile

    init_args(args)

    print(f"WORK: {get_context().config.work}")

    # Sanity check
    assert ".pytest_tmp" in get_context().config.work.parts


@pytest.fixture
def foreign_arch() -> Arch:
    """Fixture to return the foreign arch."""
    if Arch.native() == Arch.x86_64:
        return Arch.aarch64

    return Arch.x86_64


@pytest.fixture
def pmaports(pmb_args: None, monkeypatch: MonkeyPatch) -> None:
    """Fixture to clone pmaports."""

    from pmb.core import Config
    from pmb.core.context import get_context

    cfg = get_context().config

    # As an optimisation, we check the default workdir for pmaports
    # and clone it from there if it exists. This saves a bunch of bandwidth
    # and time.
    if Config.aports[-1].exists():
        # Override the URL to the local path so we can later look up the
        # remote by URL
        pmb.config.git_repos["pmaports"] = [str(Config.aports[-1])]

    if not cfg.aports[-1].exists():
        pmb.helpers.git.clone("pmaports")
        # Now operate on the cloned repo
        assert pmb.helpers.run.user(["git", "switch", "master"], working_dir=cfg.aports[-1]) == 0


@pytest.fixture
def tmp_file(tmp_path: Path) -> Path:
    return Path(tempfile.mkstemp(dir=tmp_path)[1])
