#!/usr/bin/env bash

set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

# NOTE: run-i386-qemu uses e1000 for nic. Needs to be ne2k_pci for rtems 4.x
../run-i386-qemu.sh $@ build-cmake/build-rtems6-pc686-qemu/rtems_test_suite
