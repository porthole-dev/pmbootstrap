# pmbootstrap
[**Introduction**](https://postmarketos.org/blog/2017/05/26/intro/) | [**Security Warning**](https://ollieparanoid.github.io/post/security-warning/) | [**Devices**](https://wiki.postmarketos.org/wiki/Devices)

Sophisticated chroot/build/flash tool to develop and install [postmarketOS](https://postmarketos.org).

Package build scripts live in the [`pmaports`](https://gitlab.com/postmarketOS/pmaports) repository now.

## Requirements
* 2 GB of RAM recommended for compiling
* Linux distribution on the host system (`x86`, `x86_64`, or `aarch64`)
  * [Windows subsystem for Linux (WSL)](https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux) does **not** work! Please use [VirtualBox](https://www.virtualbox.org/) instead.
  * Kernels based on the grsec patchset [do **not** work](https://github.com/postmarketOS/pmbootstrap/issues/107)
  * [Linux kernel 3.17 or higher](https://postmarketos.org/oldkernel)
* Python 3.6+
* OpenSSL
* git

## Usage Examples
Please refer to the [postmarketOS wiki](https://wiki.postmarketos.org) for in-depth coverage of topics such as [porting to a new device](https://wiki.postmarketos.org/wiki/Porting_to_a_new_device) or [installation](https://wiki.postmarketos.org/wiki/Installation_guide). The help output (`pmbootstrap -h`) has detailed usage instructions for every command. Read on for some generic examples of what can be done with `pmbootstrap`.

### Installing pmbootstrap
<https://wiki.postmarketos.org/wiki/Installing_pmbootstrap>

### Basics
Initial setup:
```
$ pmbootstrap init
```

Run this in a second window to see all shell commands that get executed:
```
$ pmbootstrap log
```

Quick health check and config overview:
```
$ pmbootstrap status
```

### Packages
Build `aports/main/hello-world`:
```
$ pmbootstrap build hello-world
```

Cross-compile to `armhf`:
```
$ pmbootstrap build --arch=armhf hello-world
```

Build with source code from local folder:
```
$ pmbootstrap build linux-postmarketos-mainline --src=~/code/linux
```

Update checksums:
```
$ pmbootstrap checksum hello-world
```

Generate a template for a new package:
```
$ pmbootstrap newapkbuild "https://gitlab.com/postmarketOS/osk-sdl/-/archive/0.52/osk-sdl-0.52.tar.bz2"
```

### Chroots
Enter the `armhf` building chroot:
```
$ pmbootstrap chroot -b armhf
```

Run a command inside a chroot:
```
$ pmbootstrap chroot -- echo test
```

Safely delete all chroots:
```
$ pmbootstrap zap
```

### Device Porting Assistance
Analyze Android [`boot.img`](https://wiki.postmarketos.org/wiki/Glossary#boot.img) files (also works with recovery OS images like TWRP):
```
$ pmbootstrap bootimg_analyze ~/Downloads/twrp-3.2.1-0-fp2.img
```

Check kernel configs:
```
$ pmbootstrap kconfig check
```

Edit a kernel config:
```
$ pmbootstrap kconfig edit --arch=armhf postmarketos-mainline
```

### Root File System
Build the rootfs:
```
$ pmbootstrap install
```

Build the rootfs with full disk encryption:
```
$ pmbootstrap install --fde
```

Update existing installation on SD card:
```
$ pmbootstrap install --sdcard=/dev/mmcblk0 --rsync
```

Run the image in QEMU:
```
$ pmbootstrap qemu --image-size=1G
```

Flash to the device:
```
$ pmbootstrap flasher flash_kernel
$ pmbootstrap flasher flash_rootfs --partition=userdata
```

Export the rootfs, kernel, initramfs, `boot.img` etc.:
```
$ pmbootstrap export
```

Extract the initramfs
```
$ pmbootstrap initfs extract
```

Build and flash Android recovery zip:
```
$ pmbootstrap install --android-recovery-zip
$ pmbootstrap flasher --method=adb sideload
```

### Repository Maintenance
List pmaports that don't have a binary package:
```
$ pmbootstrap repo_missing --arch=armhf --overview
```

Increase the `pkgrel` for each aport where the binary package has outdated dependencies (e.g. after soname bumps):
```
$ pmbootstrap pkgrel_bump --auto
```

Generate cross-compiler aports based on the latest version from Alpine's aports:
```
$ pmbootstrap aportgen binutils-armhf gcc-armhf
```

Manually rebuild package index:
```
$ pmbootstrap index
```

Delete local binary packages without existing aport of same version:
```
$ pmbootstrap zap -m
```

### Debugging
Use `-v` on any action to get verbose logging:
```
$ pmbootstrap -v build hello-world
```

Parse a single deviceinfo and return it as JSON:
```
$ pmbootstrap deviceinfo_parse pine64-pinephone
```

Parse a single APKBUILD and return it as JSON:
```
$ pmbootstrap apkbuild_parse hello-world
```

Parse a package from an APKINDEX and return it as JSON:
```
$ pmbootstrap apkindex_parse $WORK/cache_apk_x86_64/APKINDEX.8b865e19.tar.gz hello-world
```

`ccache` statistics:
```
$ pmbootstrap stats --arch=armhf
```

`distccd` log:
```
$ pmbootstrap log_distccd
```

## Development
### Requirements for running tests
* [Shellcheck](https://shellcheck.net/)

You also need to install the following python packages (pip can be useful if you distribution hasn't got them packaged):
* `pytest`
* `pytest-cov`
* `flake8`

On Alpine Linux it can be done with:
```shell
$ sudo apk add grep shellcheck py3-pytest py3-pytest-cov py3-flake8
```

### Running linters
The easiest way is to run the same script CI runs:
```shell
$ ./test/static_code_analysis.sh
```

### Running tests
You can now run `pytest -vv` inside the pmbootstrap folder to run all available tests.

CI runs slightly reduces set of tests (it skips tests that require running qemu) by this:
```shell
$ .ci/pytest.sh
```
This is the easiest way to do the same as CI.

Alternatively you can run a single test file if you wish:
```shell
$ pytest -vv ./test/test_keys.py
```

## License
[GPLv3](LICENSE)
