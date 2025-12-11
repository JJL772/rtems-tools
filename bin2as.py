#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Company    : SLAC National Accelerator Laboratory
# ----------------------------------------------------------------------------
# Description : Converts a binary file to an assembly file that can be
# included in a build. Uses the .incbin directive to link the data into the
# object with the best possible performance.
# ----------------------------------------------------------------------------
# This file is part of the rtems-tools package. It is subject to
# the license terms in the LICENSE.txt file found in the top-level directory
# of this distribution and at:
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
# No part of the rtems-tools package, including this file, may be
# copied, modified, propagated, or distributed except according to the terms
# contained in the LICENSE.txt file.
# ----------------------------------------------------------------------------
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-i', type=str, required=True, help='Input file')
parser.add_argument('-v', type=str, help='Variable name')
parser.add_argument('-o', type=str, required=True, help='Output file')

def _sanitize_name(name: str) -> str:
    return name.replace('.', '_').replace('-', '_')

def bin2as(varbase: str, input: str, output: str) -> bool:
    if not os.path.exists(input):
        return False

    sz = os.path.getsize(input)
    with open(output, 'w') as fp:
        fp.write('/** Generated file! Do not edit! **/\n\n')
        fp.write('.section .rodata\n')
        fp.write('.align 8\n\n')
        fp.write(f'{varbase}_SIZE: .long {sz}\n')
        fp.write(f'.global {varbase}_SIZE\n\n.global {varbase}\n')
        fp.write(f'{varbase}:\n')
        fp.write(f'.incbin "{os.path.abspath(input)}"\n\n')
    return True


def main():
    args = parser.parse_args()

    VARBASE = _sanitize_name(os.path.basename(args.i))
    if args.v is not None:
        VARBASE = args.v
    
    if not bin2as(VARBASE, args.i, args.o):
        exit(1)

if __name__ == '__main__':
    main()
