#!/usr/bin/env bash

set -e 

TOP="$(dirname "${BASH_SOURCE[0]}")"

if [ -z "$1" ]; then
    echo "USAGE: $0 <mybin.exe>"
    exit 1
fi

"$TOP/../host/linux-x86_64/bin/powerpc-rtems6-run" -f "$TOP/psim/psim-device-tree" "$1"

