#!/usr/bin/env bash

qemu-system-arm -no-reboot -nographic -serial none -serial mon:stdio -M xilinx-zynq-a9 -m 256M -nic user $EXTRA_ARGS -kernel $1
