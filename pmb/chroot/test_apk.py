import pytest

from pmb.core.arch import Arch
from pmb.core.context import get_context

from .apk import packages_get_locally_built_apks
import pmb.config.pmaports

@pytest.fixture
def apk_mocks(monkeypatch):
    def _pmaports_config(_aports=None):
        return {
            "channel": "edge",
    }

    monkeypatch.setattr(pmb.config.pmaports, "read_config", _pmaports_config)
    
    def _apkindex_package(_package, _arch, _must_exist=False, indexes=None):
        return {
            "name": _package,
            "version": "5.5-r0",
            "arch": str(_arch),
        }

    monkeypatch.setattr(pmb.parse.apkindex, "package", _apkindex_package)


def test_get_local_apks(pmb_args, apk_mocks):
    """Ensure packages_get_locally_built_apks() returns paths for local apks"""

    pkgname = "hello-world"
    arch = Arch.x86_64

    apk_file = get_context().config.work / "packages" / "edge" / arch / f"{pkgname}-5.5-r0.apk"
    apk_file.parent.mkdir(parents=True)
    apk_file.touch()

    local = packages_get_locally_built_apks([pkgname, "fake-package"], arch)
    print(local)
    assert len(local) == 1
    assert local[0].parts[-2:] == apk_file.parts[-2:]

