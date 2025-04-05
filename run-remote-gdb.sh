#!/usr/bin/env bash

set -e
TOP="$(realpath "$(dirname "${BASH_SOURCE[0]}")")"
echo $TOP

function usage {
    echo "USAGE: run-remote-gdb.sh -a arch [-s symfile/path.obj] [-i ip]"
}

while test $# -gt 0; do
    case $1 in
    -a)
        ARCH="$2"
        shift 2
        ;;
    --arch=*)
        ARCH="$(echo $1 | cut -d '=' -f2)"
        shift
        ;;
    -s)
        SYMFILE="$2"
        shift 2
        ;;
    --symfile=*)
        SYMFILE="$(echo $1 | cut -d '=' -f2)"
        shift
        ;;
    -i)
        IP=$2
        shift 2
        ;;
    --ip=*)
        IP="$(echo $1 | cut -d '=' -f2)"
        shift
        ;;
    -h)
        usage
        exit 0
        ;;
    *)
        ARGS="$ARGS $1"
    esac
done

if [ -z "$ARCH" ]; then
    usage
    exit 1
fi

# Custom IP provided
if [ -z "$IP" ]; then
    echo "IP defaulting to localhost:1234"
    IP="localhost:1234"
fi

ARGS="-ex \"target remote $IP\" -ex \"source $RTEMS_TOP/src/rtems-tools/tools/gdb/python/__init__.py\" "

# Exec the arm crash handler script
if [ "$ARCH" = "arm" ]; then
    ARGS="-ix \"$TOP/gdb/arm-crash.gdb\" $ARGS"
elif [ "$ARCH" = "i386" ]; then
    ARGS="-ix \"$TOP/gdb/i386-crash.gdb\" $ARGS"
fi

# We have been asked to load a symfile
if [ ! -z "$SYMFILE" ]; then
    ARGS="-ex \"set auto-load safe-path /\" -ex \"symbol-file $SYMFILE\" -ex \"b bsp_fatal_extension\" $ARGS"
fi

if [ ! -d "$TOP/../host/linux-x86_64" ]; then
    TOP="$RTEMS_TOP/tools"
fi

CMD="\"$TOP/../host/linux-x86_64/bin/$ARCH-rtems6-gdb\" $ARGS"

echo $CMD
eval $CMD
