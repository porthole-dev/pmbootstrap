# Cross Compiling

## Overview

When building packages, it might be necessary to use cross compilation
depending on the target architecture. Cross compilation is *not* necessary if
the target architecture can directly run on the host CPU (for example building
an `x86_64` or `x86` package on a `x86_64` CPU).

Multiple methods for cross compilation are implemented in pmbootstrap. For all
methods except `cross-native`, a foreign arch chroot (with the target
architecture) gets used during the build in addition to the native chroot.

<!-- markdownlint-disable MD013 MD033 -->
| Method                      | Native | Foreign | Speed  | Limitations                                                             |
|-----------------------------|--------|---------|--------|-------------------------------------------------------------------------|
| QEMU only                   |        | x       | slow   | So slow that it is desirable to<br>use other methods where possible.    |
| crossdirect<br>*(default)*  | x      | x       | medium | Cross compiler runs natively,<br>everything else goes through QEMU.     |
| cross-native                | x      |         | fast   | Cannot depend on libraries<br>(works for kernel, u-boot, etc.).         |
| cross-native2               | x      | x       | fast   | Works with e.g. meson build system.<br>Kernel builds not yet supported. |
<!-- markdownlint-enable -->

## Methods

### QEMU only

Enable this method with `options="!pmb:crossdirect"` in the `APKBUILD`.

This method is the most reliable, but also the slowest. We only use it if
faster methods don't work. GTK projects using `g-ir-scanner` (*"Generating
[…].gir with a custom command"*) are currently [known to
fail](https://gitlab.postmarketos.org/postmarketOS/pmbootstrap/-/issues/2567)
with other methods.

### Crossdirect

This is the default method.

This method works for almost all packages, and gives a good speed improvement
over running everything in QEMU. The cross compilers run natively, and with
crossdirect 5.3.1-r6 or later (porthole-dev pmaports) so do GCC's link steps:
`collect2`, `ld` and, for a package built with LTO, `lto-wrapper` and `lto1`.
The rest of the build -- the build system, generators, `meson`, `python3` --
still runs through QEMU and is still slow.

Link steps get `--sysroot=/` plus `-B/usr/lib/gcc/` and `-B/usr/lib/`, so the
driver takes the target's own GCC runtime (`crtbegin*.o`, `libgcc`,
`libstdc++`, spec files such as `libgomp.spec`) instead of the cross
toolchain's copies. The linked output is then byte-for-byte what the target's
GCC produces under QEMU, apart from the build ID. Invocations that are not
links keep running in QEMU, because their output has to describe the target's
GCC: `-E`, `-S`, `-M`, `-v`, `--version` and `-print-*` (libtool runs the
linker path that `-print-prog-name=ld` gives it, and the cross `ld` cannot run
outside crossdirect's environment), and any compiler call under `fakeroot`,
i.e. in `package()`.

The native chroot gets mounted in the foreign arch chroot at `/native`. The
[crossdirect](https://gitlab.postmarketos.org/postmarketOS/pmaports/-/blob/main/cross/crossdirect/APKBUILD)
package gets installed into the native chroot and creates wrapper scripts
pointing to the cross compilers. When building packages for `armv7`, the build
runs in the foreign chroot and `PATH` will get prepended with
`/native/usr/lib/crossdirect/armv7`. This leads to invoking the cross compiler
from the native chroot, running at native speed, whenever calling the compiler
from the foreign arch chroot.

### Cross-Native

Enable this method with `options="pmb:cross-native"` in the `APKBUILD`.

This method is only supported for packages that do not depend on foreign arch
libraries, such bare metal software (kernel, u-boot), firmware packages or the
postmarketos-artwork package.

The whole build is done in the native chroot. Environment variables are used
to tell abuild that it is a different arch package (`CARCH`) and to the
kernel-style Makefiles that the cross compilers should be used.

### Cross-Native2

Enable this method with `options="pmb:cross-native2"` in the `APKBUILD`.
This is supported since pmbootstrap 3.4, previous versions will ignore this
option and use the crossdirect method instead.

Packages from `makedepends_build=` in the `APKBUILD` are installed in the
native chroot (where we run the build), and packages from `makedepends_host=`
in the foreign chroot. Environment variables are used to run abuild in the
native chroot and use its cross compilation features rather than running it and
the build system through QEMU. This massively speeds up building when it works.

The foreign chroot is mounted into the native chroot at `/sysroot`. Most build
systems will refer to it as "sysroot", in abuild it is `CBUILDROOT`.

Packages have been built successfully with cross-native2 and the following
build systems:

* meson
* go build

Where possible, we should try to migrate all packages that currently use
crossdirect to cross-native2 to make them build faster.

## Language-specific

### Rust

Rust packages can be built with QEMU only, crossdirect, or cross-native2.

**cross-native2** is the fast one: cargo and rustc run natively and
cross-compile for the target, so build scripts and proc-macros are native too.
pmbootstrap sets `CARGO_BUILD_TARGET`, the target's linker, `--sysroot` in
`RUSTFLAGS` (target artifacts only, since a build target is set) pointing at
the target chroot (which provides the target's standard
library through its own `rust` package) and `BINDGEN_EXTRA_CLANG_ARGS_<target>`.
Put build tools (`cargo`, `cargo-auditable`, `clang-libclang` for bindgen,
`meson`, ...) in `makedepends_build`, and target libraries plus `rust` in
`makedepends_host`. A build system that locates cargo's output itself must
honour `CARGO_BUILD_TARGET`, since cargo then writes to `target/<triple>/`.

**crossdirect** runs rustc natively inside the foreign chroot. Which
architecture a crate is compiled for depends on the caller:

* cargo, through crossdirect's cargo wrapper (also for `cargo auditable`):
  crates with `--target` are for the target; build scripts, proc-macros and
  their dependencies are native. A build script that loads a target library
  at run time (bindgen and libclang) still cannot work: use cross-native2.
* anything else that calls rustc directly, like meson (mesa's nouveau, asahi
  and rusticl drivers): proc-macros are native and every other crate is for the
  target. The rlibs a proc-macro links are rebuilt for the native architecture
  on demand, from a record of how they were compiled for the target.
  `bindgen` runs natively too when the native chroot has it.

This needs crossdirect from the porthole-dev pmaports (5.3.1-r4 or later);
older crossdirect compiles every crate that meson builds for the native
architecture, and the link fails with "Relocations in generic ELF".

#### CARGO\_HOME

If a program needs to download git repositories of dependencies with cargo
(ideally they are bundled with the source tarball and don't need to be
downloaded), then these git repositories are cached with pmbootstrap. This
works as long as the program does not override
[CARGO\_HOME](https://doc.rust-lang.org/cargo/guide/cargo-home.html). GNOME
podcasts does this for example, so if building gnome-podcasts from the git
repository with `pmbootstrap build --src`, patch out the override of
`CARGO_HOME` so the dependencies do not get downloaded for every build.

#### Packaging caveats

* With crossdirect, cargo subcommands other than `build`, `test` and `run`
  (with or without `auditable`) run in QEMU, e.g. `cargo fetch`.
* Running tests doesn't really work (e.g. when building squeekboard, the tests
  hang and time out).

## Detecting cross-compilation

Sometimes, it might be desirable to have conditional logic in `APKBUILD` files
that is only executed when no cross-compilation or only certain methods of
cross-compilation are in use. For example, certain testsuites might fail if ran
with `qemu-user`.

pmbootstrap exposes the `PMB_CROSS` variable at package build time, which is
set to either `unnecessary`, `qemu-only`, `crossdirect`, `cross-native` or
`cross-native2`, depending on which method is currently in use.

To then conditionally only run tests when running natively, you can do
something like this in an `APKBUILD`:

```shell
check() {
  if [ "$PMB_CROSS" = "unnecessary" ]; then
    meson test -C build
  fi
}
```
