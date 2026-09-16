# The porthole-dev fork of pmbootstrap

This is [pmbootstrap](https://gitlab.postmarketos.org/postmarketOS/pmbootstrap)
with a short series of changes on top, used by the porthole bring-up toolkit
and by the porthole-dev package CI. The goals: build Alpine's aports
unmodified, as fast as possible, for every architecture and device upstream
supports, with no change for anything that does not use the new paths.

Nothing from this fork is sent to postmarketOS, whose policy does not accept
AI-generated contributions (see [AI.md](AI.md)).

## Install

```sh
git clone https://github.com/porthole-dev/pmbootstrap.git
cd pmbootstrap
git checkout <pinned commit>
./pmbootstrap.py --version
```

Run it from the checkout (`pmbootstrap.py`), or put a symlink to that file on
`PATH`. It needs nothing beyond what upstream pmbootstrap needs. Pin a commit,
not the branch: the branch is rebased when upstream moves.

## What differs from upstream, and why

`main` is an upstream commit plus a linear series, each commit with its tests
and documentation. `git log upstream/main..main` is the authoritative list.

- **Rust in cross-native2**: cargo cross-compiles natively and bindgen in
  build scripts works. A gtk4-rs/libcamera-rs app builds in 2m35s instead of
  more than 40 minutes under QEMU.
- **An empty assignment clears the variable**: the APKBUILD parser ignored
  `foo=`, so empty defaults stayed a literal `$foo` and subpackages kept the
  `depends` they should have cleared.
- **`$CARCH` conditionals are evaluated for the target arch**: abuild picks
  depends, makedepends and subpackages per `$CARCH`, and pmbootstrap skipped
  those blocks, so Alpine's mesa was built without bindgen.
- **envkernel builds kernels with ccache**: its make alias disabled ccache for
  every kernel compile.
- **`helpers/apkbuild-vs-shell.py`**: checks the APKBUILD parser against
  busybox sh over whole aports trees, before and after a change.
- **`find()` finds arch-dependent subpackages** such as
  `mesa-vulkan-freedreno`, without parsing all of pmaports.
- **`build --ignore-depends` works**: the option was parsed and never
  applied.
- **crossdirect Rust's native chroot gets build dependencies only, from
  binary repositories**: runtime depends, or a newer pmaports fork of a
  library, made pmbootstrap build whole packages for the native arch first.
- **Packages carry the commit they were built from**: abuild looked for git in
  the copy of the aport inside the chroot, so every apk said
  `commit = -dirty` and got the build time as its date. pmbootstrap now reads
  the aport's checkout and passes `ABUILD_LAST_COMMIT` and
  `SOURCE_DATE_EPOCH`.
- **One sccache server per chroot**: sccache's default TCP port is shared by
  every chroot and work dir on the host, so one build's server compiled
  another work dir's crates against the wrong root and failed them.

The changes that make crossdirect faster live in pmaports, because crossdirect
is an aport (`cross/crossdirect` in the porthole-dev pmaports): GCC links,
including LTO, run natively instead of under QEMU; rustc called directly by
meson compiles target crates for the target and proc-macros natively; `cargo
auditable build` no longer falls back to QEMU; and `bindgen` runs natively.
See [docs/cross_compiling.md](docs/cross_compiling.md).

## Update from upstream

```sh
git fetch upstream
git rebase --onto upstream/main <old upstream commit> main
```

Then, before moving the pin:

```sh
pytest -m "not skip_ci"
ruff check        # no findings beyond those on upstream/main
ruff format --diff
mypy .
```

and, in a container (it runs APKBUILD code), compare the parser with the
shell against an upstream checkout of the same commit:

```sh
git worktree add /tmp/pmb-upstream upstream/main
find aports pmaports -name APKBUILD | xargs \
    helpers/apkbuild-vs-shell.py --baseline /tmp/pmb-upstream
```

It must report no regressions and no new errors. Drop a commit from the
series when upstream has an equivalent.

The remote `upstream` is fetch-only; its push URL is deliberately invalid.
