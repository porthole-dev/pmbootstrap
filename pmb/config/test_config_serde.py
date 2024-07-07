from pathlib import Path
import pytest

import pmb.config
from pmb.core.config import SystemdConfig

"""Test the config file serialization and deserialization."""


def test_load(config_file):
    config = pmb.config.load(config_file)
    assert config.build_default_device_arch
    assert config.ccache_size == "5G"
    assert config.device == "qemu-amd64"
    assert config.extra_packages == "neofetch,neovim,reboot-mode"
    assert config.hostname == "qemu-amd64"
    assert not config.is_default_channel
    assert config.jobs == "8"
    assert config.kernel == "edge"
    assert config.locale == "C.UTF-8"
    assert config.ssh_keys
    assert config.sudo_timer
    assert config.systemd == SystemdConfig.ALWAYS
    assert config.timezone == "Europe/Berlin"
    assert config.ui == "gnome"
    assert config.providers == {}
    assert config.mirrors["pmaports"] is not None
    assert ".pytest_tmp" in config.work.parts


@pytest.fixture
def config_file_2_3_x(tmp_path: Path):
    """Fixture to create a temporary pmbootstrap_v3.cfg file with 2.3.x format."""
    file = tmp_path / "pmbootstrap_v3.cfg"
    contents = """[pmbootstrap]
aports = /home/user/.local/var/pmbootstrap/cache_git/pmaports
ccache_size = 32G
is_default_channel = False
device = oneplus-fajita
extra_packages = none
hostname = pmos
build_pkgs_on_install = True
jobs = 32
kernel = edge
keymap =
locale = C.UTF-8
nonfree_firmware = True
nonfree_userland = False
ssh_keys = True
timezone = Europe/London
ui = gnome-mobile
ui_extras = False
user = user
work = /home/user/.local/var/pmbootstrap
boot_size = 256
extra_space = 0
sudo_timer = True
mirrors_postmarketos = http://mirror.postmarketos.org/postmarketos/
mirror_alpine = http://dl-cdn.alpinelinux.org/alpine/
ssh_key_glob = ~/.ssh/id_*.pub
qemu_redir_stdio = True
build_default_device_arch = True
merge_usr = True
auto_checksum = True
systemd = always

[providers]

"""

    open(file, "w").write(contents)
    return file


def test_migrate_2_to_3(config_file_2_3_x, tmp_path, monkeypatch):
    tmp_path = tmp_path / "pmbootstrap-new.cfg"

    did_migrate = False

    def mock_save(path, config):
        nonlocal did_migrate
        did_migrate = True

    monkeypatch.setattr(pmb.config.file, "save", mock_save)

    config = pmb.config.load(config_file_2_3_x)

    # The 2.3.x to 3.0 migration removes these keys from the
    # config in favour of a new [mirrors] section.
    # It should be automatically migrated.
    assert not hasattr(config, "mirror_alpine")
    assert not hasattr(config, "mirrors_postmarketos")

    # Check that save was called (which happens on a config migration)
    assert did_migrate


# FIXME: add save tests and better type checks
