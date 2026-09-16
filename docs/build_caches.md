# Build caches

Everything pmbootstrap caches lives in the work directory, next to the
chroots. Only the caches are worth keeping between builds or restoring in CI;
the chroots are rebuilt from packages in seconds.

<!-- markdownlint-disable MD013 -->
| Directory                 | What it holds                                          | Written by                      |
|---------------------------|--------------------------------------------------------|---------------------------------|
| `cache_ccache_$ARCH`      | ccache: compiled C/C++ objects                         | every package build             |
| `cache_sccache`           | sccache: compiled Rust crates                          | Rust builds without crossdirect |
| `cache_rust`              | cargo registry and git checkouts                       | Rust builds                     |
| `cache_go`                | `GOCACHE` and `GOMODCACHE`                             | Go builds                       |
| `cache_distfiles`         | source tarballs abuild downloaded                      | every package build             |
| `cache_apk_$ARCH`         | apks downloaded from the mirrors                       | every chroot                    |
| `cache_git`, `cache_http` | git clones (pmaports, aports), APKINDEX and apk.static | pmbootstrap itself              |
<!-- markdownlint-enable -->

`$ARCH` is the architecture of the *chroot the build runs in*, which is not
always the architecture of the package. A crossdirect build of an aarch64
package runs the native cross compiler, but from inside the foreign chroot,
so its objects land in `cache_ccache_aarch64` next to the ones a QEMU-only
build of the same package writes. They do not collide -- ccache hashes the
compiler binary -- but they do not share either: moving a package between
QEMU-only and crossdirect starts from a cold cache. A cross-native build (the
kernel) runs in the native chroot, and its objects go to
`cache_ccache_x86_64`, not to the target's cache.

## Sharing one cache between work directories

Two work directories (a second checkout, a test work dir, a `--work`
elsewhere) each have their own caches and share nothing. Point them at one
directory with a symlink, before the first build:

```shell
ln -sfn /srv/pmb-cache/ccache_aarch64 "$WORK/cache_ccache_aarch64"
ln -sfn /srv/pmb-cache/distfiles "$WORK/cache_distfiles"
```

pmbootstrap bind-mounts these into the chroots and follows the symlink.
Measured: libcamera built in a second, empty work directory (new chroots,
freshly installed compilers) took 2m17s with 268 of 274 cacheable compiles
served from the first work directory's ccache, against 5m00s cold.

ccache is safe for several builds using one cache directory at the same time.
sccache is not: it keeps one server per cache directory and accounts for the
cache size in that server, so share `cache_sccache` only between work
directories that do not build at the same time.

## CI

Restore and save the caches, not the work directory. A job that builds one
package at a time wants one cache entry per package, because that keeps each
entry small enough for a cache service with a size limit (GitHub: 10 GB per
repository, least recently used entries are evicted):

```yaml
- uses: actions/cache@v6
  with:
    path: |
      ${{ runner.temp }}/work/cache_ccache_aarch64
      ${{ runner.temp }}/work/cache_sccache
      ${{ runner.temp }}/work/cache_rust
      ${{ runner.temp }}/work/cache_go
      ${{ runner.temp }}/work/cache_distfiles
    key: pmb-build-aarch64-${{ matrix.package }}-${{ github.run_id }}
    restore-keys: pmb-build-aarch64-${{ matrix.package }}-
```

A key that ends in the run id is never restored, only saved, and
`restore-keys` then picks the newest entry of the same package: every run
saves a fresh entry and starts from the previous one. Keep the apk cache in
its own entry (`pmb-apk-aarch64-...`), because every package's job fills it
with the same downloads.

Two things make a restored cache useless, and both are easy to miss:

* **Ownership.** Builds run as uid 12345 inside the chroots, while the cache
  comes back owned by the runner. `chown -R 12345:12345` the ccache and
  distfiles directories after restoring them.
* **Size.** `ccache_size` is 5G per architecture by default, which one large
  package can fill and which is half of a repository's whole cache budget.
  `pmbootstrap config ccache_size 2G` keeps an entry restorable.
