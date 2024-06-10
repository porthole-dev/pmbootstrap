import os
from pathlib import Path
import pytest
from contextlib import contextmanager

@contextmanager
def _fixture_context(val):
    yield val

@pytest.fixture(scope="session")
def config_file_session(tmp_path_factory):
    """Fixture to create a temporary pmbootstrap.cfg file."""
    tmp_path = tmp_path_factory.mktemp("pmbootstrap")
    file = tmp_path / "pmbootstrap.cfg"
    workdir = tmp_path / "work"
    workdir.mkdir()
    contents = """[pmbootstrap]
build_default_device_arch = True
ccache_size = 5G
device = qemu-amd64
extra_packages = neofetch,neovim,reboot-mode
hostname = qemu-amd64
is_default_channel = False
jobs = 8
kernel = edge
locale = C.UTF-8
ssh_keys = True
sudo_timer = True
systemd = always
timezone = Europe/Berlin
ui = gnome
work = {0}

[providers]

[mirrors]
""".format(workdir)

    open(file, "w").write(contents)
    return file


@pytest.fixture
def config_file(config_file_session):
    """Fixture to create a temporary pmbootstrap.cfg file."""
    with _fixture_context(config_file_session) as val:
        yield val


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


# FIXME: get_context() at runtime somehow doesn't return the
# custom context we set up here.
# @pytest.fixture(scope="session")
# def pmb_args(config_file_session):
#     """This is (still) a hack, since a bunch of the codebase still
#     expects some global state to be initialised. We do that here."""

#     from pmb.types import PmbArgs
#     from pmb.helpers.args import init as init_args

#     args = PmbArgs()
#     args.config = config_file_session
#     args.aports = None
#     args.timeout = 900
#     args.details_to_stdout = False
#     args.quiet = False
#     args.verbose = False
#     args.offline = False
#     args.action = "init"
#     args.cross = False
#     args.log = Path()

#     print("init_args")
#     return init_args(args)

@pytest.fixture
def foreign_arch():
    """Fixture to return the foreign arch."""
    from pmb.core.arch import Arch
    if os.uname().machine == "x86_64":
        return Arch.aarch64

    return Arch.x86_64

