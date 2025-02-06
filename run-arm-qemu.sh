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

CMD="qemu-system-arm -no-reboot -net nic,model=cadence_gem -nographic -serial none -serial mon:stdio -M xilinx-zynq-a9 -m 256M $ARGS -kernel \"$KERNEL\""

echo "$CMD"
eval $CMD

#"$TOP/src/rtems-tools/tester/rtems-run" --rtems-bsp=xilinx_zynq_a9_qemu --rtems-tools="$TOP/host/linux-x86_64" $@
