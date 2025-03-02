#!/usr/bin/env python3

# Script to generate a "rootfs" from a directory

import argparse
import configparser
import os

parser = argparse.ArgumentParser()
parser.add_argument('-i', type=str, required=True, help='Directory containing rootfs and config file')
parser.add_argument('-o', type=str, required=True, help='Resulting C source file')

class RootfsFile:
    def __init__(self, name: str, bits: int, uid: int, gid: int):
        self.name = name
        self.bits = bits
        self.uid = uid
        self.gid = gid


def parse_config(dir: str) -> list[RootfsFile]:
    if not os.path.exists(f'{dir}/rootfs.txt'):
        print('No rootfs.txt in the rootfs directory, aborting')
        exit(1)

    lines = []
    with open(f'{dir}/rootfs.txt') as fp:
        lines = fp.readlines()
    
    files: list[RootfsFile] = []
    for l in lines:
        t = l.split(' ')
        m = []
        for i in range(len(t)):
            if t[i].startswith('#'): break
            if len(t[i]) < 1: continue
            m.append(t[i])

        if len(m) > 0:
            files.append(RootfsFile(m[0], int(m[1]) if len(m) > 1 else 0o644,
                                    int(m[2]) if len(m) > 2 else 0,
                                    int(m[3]) if len(m) > 3 else 0))
    return files

def main():
    args = parser.parse_args()
    files = parse_config(args.i)    
    with open(args.o, 'w') as fp:
        fp.write('// WARNING: This was generated using mkrootfs.py!\n\n')
        fp.write('#include <rtems.h>\n#include <rtems/shell.h>\n#include <unistd.h>\n#include <stdio.h>\n\n')
        # File contents
        for f in files:
            fp.write(f'const char* {f.name.replace('/', '_').replace('.', '_').upper()} = \n')
            with open(f'{args.i}/{f.name}', 'r') as ip:
                lines=ip.readlines()
                for l in lines:
                    fp.write(f'  \"{l.replace('\\', '\\\\').rstrip()}\\n\"\n')
            fp.write(';\n\n')
        # Generator
        fp.write('void unpack_rootfs()\n{\n')
        fp.write('  printf("Unpacking rootfs...\\n");\n\n')
        for f in files:
            fp.write(f'  rtems_mkdir(\"{os.path.dirname(f.name)}\", 0777);\n')
            fp.write(f'  rtems_shell_write_file(\"{f.name}\", {f.name.replace('/', '_').replace('.', '_').upper()});\n')
            fp.write(f'  chmod(\"{f.name}\", {f.bits});\n')
            fp.write(f'  chown(\"{f.name}\", {f.uid}, {f.gid});\n\n')
        fp.write('}\n')
    

if __name__ == '__main__':
    main()