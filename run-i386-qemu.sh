#!/usr/bin/env bash

set -e

TOP="$(realpath "$(dirname "${BASH_SOURCE[0]}")/../")"

ARGS=
KERNEL=
while test $# -gt 0; do
    case $1 in
    --gdb)
        ARGS="$ARGS -s -S"
        shift
        ;;
    --gdb=*)
        ARGS="$ARGS --gdb tcp::$(echo $1 | cut -d '=' -f 1) -S"
        shift
        ;;
    -*)
        echo "Unknown argument $1"
        exit 1
        ;;
    *)
        KERNEL="$1"
        shift
        ;;
    esac
done

if [ -z "$KERNEL" ]; then
    echo "USAGE: $0 <path-to-exe>"
    exit 1
fi

#     * start qemu like this
#     * qemu-system-i386 -m 64 -no-reboot -serial stdio -display none \
#     * -net nic,model=e1000 -net user,restrict=yes \
#     * -append "--video=off --console=/dev/com1" -kernel libComTestHarness
#CMD="qemu-system-i386 -no-reboot -net nic,model=cadence_gem -nographic -serial none -serial mon:stdio -M xilinx-zynq-a9 -m 256M $ARGS -kernel \"$KERNEL\""
CMD="qemu-system-i386 -m 64 -no-reboot -serial mon:stdio -nographic -net nic,model=e1000 -net user,restrict=yes -append \"--video=off --nodhcp --console=/dev/com1\" $ARGS -kernel \"$KERNEL\""

echo "$CMD"
eval $CMD

