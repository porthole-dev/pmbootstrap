
import multiprocessing
from typing import List, Dict
from pathlib import Path
import os

class Config():
    aports: List[Path] = [Path(os.path.expanduser("~") +
                        "/.local/var/pmbootstrap/cache_git/pmaports")]
    boot_size: int = 256
    build_default_device_arch: bool = False
    build_pkgs_on_install: bool = True
    ccache_size: str = "5G" # yeahhhh this one has a suffix
    device: str = "qemu-amd64"
    extra_packages: str = "none"
    extra_space: int = 0
    hostname: str = ""
    is_default_channel: bool = True
    jobs: str = str(multiprocessing.cpu_count() + 1)
    kernel: str = "stable"
    keymap: str = ""
    locale: str = "en_US.UTF-8"
    # NOTE: mirrors use http by default to leverage caching
    mirror_alpine: str = "http://dl-cdn.alpinelinux.org/alpine/"
    # NOTE: mirrors_postmarketos variable type is supposed to be
    #       comma-separated string, not a python list or any other type!
    mirrors_postmarketos: List[str] = ["http://mirror.postmarketos.org/postmarketos/"]
    qemu_redir_stdio: bool = False
    ssh_key_glob: str = "~/.ssh/id_*.pub"
    ssh_keys: bool = False
    sudo_timer: bool = False
    systemd: str = "default"
    timezone: str = "GMT"
    ui: str = "console"
    ui_extras: bool = False
    user: str = "user"
    work: Path = Path(os.path.expanduser("~") + "/.local/var/pmbootstrap")

    providers: Dict[str, str] = { }
