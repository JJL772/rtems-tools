#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Company    : SLAC National Accelerator Laboratory
# ----------------------------------------------------------------------------
# Description : Symbol diffing utility
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
import subprocess

parser = argparse.ArgumentParser(description='Given a base image and list of loadable objects, check for undefined symbols in the objects')
parser.add_argument('-b', type=str, required=True, help='Base image ELF file')
parser.add_argument('-C', type=str, required=True, help='Target prefix for nm (i.e. powerpc-rtems7)')
parser.add_argument('-l', action='append', help='List of loadable objects to analyze. Loaded in order of their appearance on the command line')

def _get_symbols(nm: str, object: str) -> tuple[set, set]:
    """
    Returns a tuple of undefined and defined symbols in the specified ELF file.

    Parameters
    ----------
    nm : str
        Name of the NM executable
    object : str
        Path to the ELF file
    
    Returns
    -------
    tuple[str,str]
        (undef, defined) symbols
    """
    r = subprocess.run([nm, '-fposix', object], capture_output=True, universal_newlines=True)
    if r.returncode != 0:
        raise RuntimeError(f'{nm} returned {r.returncode}')
    lines = r.stdout.splitlines()
    undef = set()
    defined = set()
    for l in lines:
        c = l.split(' ')
        if len(c) < 2: continue
        match c[1]:
            case 'U':
                if c[0] not in defined:
                    undef.add(c[0])
            case _:
                defined.add(c[0])
                if c[0] in undef:
                    undef.remove(c[0])
    return (undef, defined)


def _get_nm(pfx: str):
    return f'{pfx}-nm'

def main():
    args = parser.parse_args()
    NM = _get_nm(args.C)

    base_undef, base_def = _get_symbols(NM, args.b)

    if not args.l:
        print('No libraries specified')
        exit(1)

    for lib in args.l:
        ud, d = _get_symbols(NM, lib)
        s = ud.difference(base_def)
        if len(s) > 0:
            print('\n'.join(s))
            exit(1)

if __name__ == '__main__':
    main()