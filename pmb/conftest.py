import os
from pathlib import Path
import pytest
import shutil

import pmb.core
from pmb.types import PmbArgs
from pmb.helpers.args import init as init_args

_testdir = Path(__file__).parent / "data/tests"

@pytest.fixture
def config_file(tmp_path_factory):
    """Fixture to create a temporary pmbootstrap.cfg file."""
    tmp_path = tmp_path_factory.mktemp("pmbootstrap")
    out_file = tmp_path / "pmbootstrap.cfg"
    workdir = tmp_path / "work"
    workdir.mkdir()

    file = _testdir / "pmbootstrap.cfg"
    contents = open(file).read().format(workdir)

    open(out_file, "w").write(contents)
    return out_file


@pytest.fixture
def device_package(config_file):
    """Fixture to create a temporary deviceinfo file."""
    MOCK_DEVICE = "qemu-amd64"
    pkgdir = config_file.parent / f"device-{MOCK_DEVICE}"
    pkgdir.mkdir()

    for file in ["APKBUILD", "deviceinfo"]:
        shutil.copy(_testdir / f"{file}.{MOCK_DEVICE}",
                    pkgdir / file)

    return pkgdir


@pytest.fixture
def mock_devices_find_path(device_package, monkeypatch):
    """Fixture to mock pmb.helpers.devices.find_path()"""
    def mock_find_path(device, file=''):
        print(f"mock_find_path({device}, {file})")
        out = device_package / file
        if not out.exists():
            return None

        return out

    monkeypatch.setattr("pmb.helpers.devices.find_path", mock_find_path)


@pytest.fixture(autouse=True)
def setup_logging(tmp_path: Path):
    """Setup logging for all tests."""
    import logging
    logfile = tmp_path / "test.log"
    logging.basicConfig(level=logging.DEBUG, force=True, filename=logfile)


@pytest.fixture(autouse=True)
def setup_mock_ask(monkeypatch):
    """Common setup to mock cli.ask() to avoid reading from stdin"""
    import pmb.helpers.cli

    def mock_ask(question="Continue?", choices=["y", "n"], default="n",
                 lowercase_answer=True, validation_regex=None, complete=None):
        return default

    monkeypatch.setattr(pmb.helpers.cli, "ask", mock_ask)


# FIXME: get/set_context() is a bad hack :(
@pytest.fixture
def mock_context(monkeypatch):
    """Mock set_context() to bypass sanity checks. Ideally we would
    mock get_context() as well, but since every submodule of pmb imports
    it like "from pmb.core.context import get_context()", we can't
    actually override it with monkeypatch.setattr(). So this is the
    best we can do... set_context() is only called from one place and is
    done so with the full namespace, so this works."""

    def mock_set_context(ctx):
        print(f"mock_set_context({ctx})")
        setattr(pmb.core.context, "__context", ctx)

    monkeypatch.setattr("pmb.core.context.set_context", mock_set_context)


# FIXME: get_context() at runtime somehow doesn't return the
# custom context we set up here.
@pytest.fixture
def pmb_args(config_file, mock_context):
    """This is (still) a hack, since a bunch of the codebase still
    expects some global state to be initialised. We do that here."""

    args = PmbArgs()
    args.config = config_file
    args.aports = None
    args.timeout = 900
    args.details_to_stdout = False
    args.quiet = False
    args.verbose = False
    args.offline = False
    args.action = "init"
    args.cross = False
    args.log = Path()

    print("init_args")
    init_args(args)

@pytest.fixture
def foreign_arch():
    """Fixture to return the foreign arch."""
    from pmb.core.arch import Arch
    if os.uname().machine == "x86_64":
        return Arch.aarch64

    return Arch.x86_64

