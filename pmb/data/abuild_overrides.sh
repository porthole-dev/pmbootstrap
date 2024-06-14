# shellcheck shell=sh
# BEGIN PMBOOTSTRAP OVERRIDES

# Patched version of verify() to only warn instead of
# refusing to build.
# shellcheck disable=SC2034,SC2154,SC3043
verify() {
	rm -f /tmp/apkbuild_verify_failed
	local verified=false algo=
	sumcheck "sha512" "$sha512sums" && verified=true
	if [ -n "$source" ] && ! $verified; then
		touch /tmp/apkbuild_verify_failed
	fi
	return 0
}

# END PMBOOTSTRAP OVERRIDES
