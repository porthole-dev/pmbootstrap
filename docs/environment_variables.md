# Environment Variables

## `PMB_SUDO`

pmbootstrap supports `doas` and `sudo`. If multiple sudo implementations are
installed, pmbootstrap will use `doas`. You can set the `PMB_SUDO`
environmental variable to define the sudo implementation you want to use.

## `PMB_APK_FORCE_MISSING_REPOSITORIES`

When this is set to `1`, pmbootstrap will not complain if downloading an
APKINDEX results in a 404 not found error. This is used by
[bpo](https://build.postmarketos.org) when building a new stable repository for
the first time. For example if the `x86_64` repository was already built and
published, but the `aarch64` repository wasn't published yet.
