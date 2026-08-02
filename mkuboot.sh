#!/usr/bin/env bash
set -e

rtv="7"

while getopts "f:o:a:l:r:" opt; do
    case "${opt}" in
        f)
            file="${OPTARG}"
            ;;
        o)
            out="${OPTARG}"
            ;;
        a)
            arch="${OPTARG}"
            ;;
        l)
            loadaddr="${OPTARG}"
            ;;
		r)
			rtv="${OPTARG}"
			;;
        *)
            echo "USAGE: $0 -f FILE -o OUT -a ARCH -l LOADADDR [-r RTEMS_VER]"
            exit 1
            ;;
    esac
done

if [ -z "${out}" ] || [ -z "${arch}" ] || [ -z "${file}" ] || [ -z "${loadaddr}" ]; then
    echo "USAGE: $0 -f FILE -o OUT -a ARCH -l LOADADDR [-r RTEMS_VER]"
    exit 1
fi

echo "Generating flag binary ${file}.bin"
${arch}-rtems${rtv}-objcopy -Obinary "${file}" "${file}.bin"

uboot_arch="${arch}"
if [ "${arch}" = "aarch64" ]; then
    uboot_arch="arm64"
fi

echo "Gzipping ${file}..."
gzip -9 "${file}.bin" -S .gz -k -f

echo "Generating u-boot image ${out}"
mkimage \
    -A ${uboot_arch} \
    -O rtems \
    -T kernel \
    -a ${loadaddr} \
    -e ${loadaddr} \
    -n RTEMS \
    -d "${file}.bin.gz" \
    "${out}"

echo "Wrote ${out}"
