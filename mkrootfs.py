#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Company    : SLAC National Accelerator Laboratory
# ----------------------------------------------------------------------------
# Description : Tool to generate a rootfs from a directory
# ----------------------------------------------------------------------------
# This file is part of the rtems-tools package. It is subject to
# the license terms in the LICENSE.txt file found in the top-level directory
# of this distribution and at:
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
# No part of the rtems-tools package, including this file, may be
# copied, modified, propagated, or distributed except according to the terms
# contained in the LICENSE.txt file.
# ----------------------------------------------------------------------------
import argparse
import os
import sys
import string
import tarfile

import bin2as

parser = argparse.ArgumentParser()
parser.add_argument('-i', type=str, required=True, help='Directory containing rootfs and config file')
parser.add_argument('-o', type=str, required=True, help='Resulting C source file')
parser.add_argument('-t', action='store_true', help='Generate a tarball rootfs')
parser.add_argument('-m', action='append', help='Define macro for substitution')
parser.add_argument('-n', type=str, help='For embedded tarfs, generate an array with this name')

class RootfsFile:
    def __init__(self, name: str, dest: str, bits: str, uid: str, gid: str):
        self.name = name
        self.bits = bits
        self.dest = dest
        self.uid = uid
        self.gid = gid

    def get_arch_name(self) -> str:
        return self.name if self.dest == '/' else self.dest

    def get_abs_path(self, rel: str) -> str:
        if self.name.startswith('/'):
            return self.name
        return f'{rel}/{self.name}'


def _clean_fn(file: str) -> str:
    return file.replace('/', '_').replace('.', '_').replace('-', '_').upper()

def _bin2c(file: str, out: str, name: str):
    """
    Embeds a file into an array in a C file.
    Replicates the behavior of bin2c

    Parameters
    ----------
    file : str
        Input file to embed
    out : str
        Output .c file
    """
    with open(out, 'w') as wp:
        wp.write('/** WARNING: generated file! **/\n\n')
        wp.write('#include <stddef.h>\n#include <stdint.h>\n\n')
        wp.write(f'const unsigned char {name}[] = {{\n')
        with open(file, 'rb') as fp:
            b = fp.read(16)
            while len(b) > 0:
                wp.write('  ')
                for byte in b:
                    wp.write(f'{hex(byte)},')
                wp.write('\n')
                b = fp.read(16)
        wp.write('};\n\n')
        wp.write(f'const size_t {name}_SIZE = sizeof({name});\n\n')
            


def _escape_quotes(l: str) -> str:
    """
    Escape quotes on a line
    """
    return l.replace("\\", "\\\\").replace("\"", "\\\"").rstrip()

def _parse_config(dir: str, macros: dict) -> list[RootfsFile]:
    """
    Parse the rootfs configuration file

    Parameters
    ----------
    dir : str
        Path to the directory containing the rootfs and its config file
    macros : dict
        Macros for string substitution
    """
    if not os.path.exists(f'{dir}/rootfs.txt'):
        print('No rootfs.txt in the rootfs directory, aborting')
        exit(1)

    lines = []
    with open(f'{dir}/rootfs.txt') as fp:
        lines = fp.readlines()
    
    files: list[RootfsFile] = []
    for l in lines:
        l = string.Template(l).substitute(macros).strip()
        t = l.split(' ')
        m = []
        for i in range(len(t)):
            if t[i].startswith('#'): break
            if len(t[i]) < 1: continue
            m.append(t[i])

        if len(m) > 0:
            files.append(RootfsFile(m[0],
                                    m[1].rstrip() if len(m) > 1 else '/',
                                    m[2].rstrip() if len(m) > 2 else '0644',
                                    m[3].rstrip() if len(m) > 3 else '0',
                                    m[4].rstrip() if len(m) > 4 else '0'))
    return files

def generate_source(dir: str, out: str, macros: dict):
    """
    Generate a rootfs.c file, instead of using the tarball method

    Parameters
    ----------
    dir : str
        Rootfs directory
    out : str
        Output file
    macros : dict
        Macros for string substitution
    """
    files = _parse_config(dir, macros)    
    with open(out, 'w') as fp:
        fp.write(f'// WARNING: This was generated using "{" ".join(sys.argv)}"\n// DO NOT MODIFY!\n\n')
        fp.write('#include <rtems.h>\n#include <rtems/shell.h>\n#include <unistd.h>\n#include <stdio.h>\n\n')
        # File contents
        for f in files:
            fp.write(f'const char* {_clean_fn(f.name)} = \n')
            with open(f'{dir}/{f.name}', 'r') as ip:
                lines=ip.readlines()
                for l in lines:
                    fp.write(f'  \"{_escape_quotes(l)}\\n\"\n')
            fp.write(';\n\n')
        # Generator
        fp.write('void unpack_rootfs()\n{\n')
        fp.write('  printf("Unpacking rootfs...\\n");\n\n')
        for f in files:
            fp.write(f'  rtems_mkdir(\"{os.path.dirname(f.name)}\", 0777);\n')
            fp.write(f'  rtems_shell_write_file(\"{f.name}\", {_clean_fn(f)});\n')
            fp.write(f'  chmod(\"{f.name}\", {f.bits});\n')
            fp.write(f'  chown(\"{f.name}\", {f.uid}, {f.gid});\n\n')
        fp.write('}\n')


def generate_tarball(dir: str, out: str, macros: dict):
    """
    Generate a rootfs.c that encodes a tar file to be used with rtems tarfs

    Parameters
    ----------
    dir : str
        Rootfs directory
    out : str
        Output file
    macros : dict
        Macros for string substitution
    """
    files = _parse_config(dir, macros)
    tf = tarfile.TarFile(f'{out}.tar', 'w')

    def filt(file: RootfsFile, ti: tarfile.TarInfo) -> tarfile.TarInfo | None:
        ti.uid = int(file.uid)
        ti.gid = int(file.gid)
        ti.mode = int(file.bits, base=8)
        ti.type = tarfile.REGTYPE
        return ti

    for file in files:
        ti=tarfile.TarInfo()
        tf.add(file.get_abs_path(dir), file.get_arch_name(), True,
               filter = lambda x : filt(file, x))

    tf.close()
    bin2as.bin2as('tar_rootfs', f'{out}.tar', out)


def main():
    args = parser.parse_args()

    macros = {}
    if args.m is not None:
        for a in args.m:
            s = a.find('=')
            macros[a[:s]] = a[s+1:]

    print(macros)

    if args.t:
        generate_tarball(args.i, args.o, macros)
    else:
        generate_source(args.i, args.o, macros)


if __name__ == '__main__':
    main()