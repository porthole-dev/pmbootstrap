import pytest

import pmb.helpers.git
import pmb.helpers.run
from pmb.core.pkgrepo import pkgrepo_paths, pkgrepo_default_path


@pytest.mark.parametrize("config_file", ["no-repos"], indirect=True)
def test_pkgrepo_paths_no_repos(pmb_args):
    """Test pkgrepo_paths() with no repositories. Should raise a RuntimeError."""
    pkgrepo_paths.cache_disable()
    with pytest.raises(RuntimeError):
        paths = pkgrepo_paths()
        print(paths)


def test_pkgrepo_pmaports(pmaports, monkeypatch):
    """Test pkgrepo_paths() with pmaports repository and systemd extra repo"""

    # Disable results caching
    pkgrepo_paths.cache_disable()
    pkgrepo_default_path.cache_disable()

    paths = pkgrepo_paths()
    print(f"[master] pkgrepo_paths: {paths}")
    assert len(paths) == 1
    assert "pmaports" in paths[0].name

    default_path = pkgrepo_default_path()

    assert default_path.name == "pmaports"

    # Test extra-repos
    assert (
        pmb.helpers.run.user(
            ["git", "checkout", "master_staging_systemd"], working_dir=default_path
        )
        == 0
    )

    paths = pkgrepo_paths(with_extra_repos="disabled")
    assert len(paths) == 1

    paths = pkgrepo_paths(with_extra_repos="enabled")
    assert len(paths) == 2

    # systemd is the first path, since we want packages there to take priority
    assert paths[0].name == "systemd"
    # but pmaports is the default rep, since it has channels.cfg/pmaports.cfg
    assert pkgrepo_default_path().name == "pmaports"
