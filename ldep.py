#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Company    : SLAC National Accelerator Laboratory
# ----------------------------------------------------------------------------
# Description : Wrapper around the ldep utility by Till Straumann. 
# Automatically invokes nm to generate the symbols lists, and then ldep on top 
# of those.
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

parser = argparse.ArgumentParser()
parser.add_argument('-l', metavar='lib', action='append', help='Library to search in')
parser.add_argument('-L', metavar='dir', action='append', help='Additional library search paths')
parser.add_argument('-v', action='store_true', help='Verbose')
parser.add_argument('-C', type=str, metavar='prefix', default='', help='Compiler prefix (i.e. powerpc-rtems6 for powerpc-rtems6-gcc)')
parser.add_argument('-O', type=str, metavar='dir', default='/tmp', help='Output directory for temporary files')
parser.add_argument('-c', type=str, metavar='file', default=None, help='Generate Cexpsh symbol list')
parser.add_argument('-e', type=str, metavar='file', default=None, help='Generate linker script')


def _get_tool_name(pfx: str, tool: str) -> str:
    """
    Returns the tool name based on tool prefix (if any)
    """
    if len(pfx) > 0:
        return f'{pfx}-{tool}'
    return tool

def _get_compiler_lib_paths(compiler: str) -> list[str]:
    """
    Returns a list of compiler library search paths
    """
    r = subprocess.run([compiler, '-print-search-dirs'], capture_output=True, universal_newlines=True)
    if r.returncode != 0:
        return []
    lines = [x for x in r.stdout.splitlines() if x.startswith('libraries:')]
    return [x.removeprefix(' =') for x in lines[0].split(':') if x != 'libraries']

def _find_lib(paths: list[str], lib: str) -> str | None:
    """
    Tries to find a library based on the provided library search paths
    """
    for p in paths:
        if os.path.exists(f'{p}/lib{lib}.a'):
            return f'{p}/lib{lib}.a'
    return None

def _gen_symbols(nm: str, odir: str, lib: str) -> str | None:
    """
    Generates a list of symbols for a library using nm
    """
    r = subprocess.run(
        [nm, '-g', '-fposix', lib],
        capture_output=True,
        universal_newlines=True
    )
    if r.returncode != 0:
        return None
    # write out a file
    file = f'{odir}/{os.path.basename(lib)}.nm'
    with open(file, 'w') as fp:
        fp.write(r.stdout)
    return f'{odir}/{os.path.basename(lib)}.nm'

def _gen_symbols_for_libs(nm: str, odir: str, libs: list[str], dirs: list[str]) -> list[str] | None:
    """
    Given a list of libraries and library directories, generate .nm files for each of them,
    returning a list of the resulting files.
    """
    nms = []
    for l in libs:
        lib = _find_lib(dirs, l)
        if lib is None:
            return False
        n = _gen_symbols(nm, odir, lib)
        if n is None:
            return None
        nms.append(n)
    return nms

def _run_ldep(nm_files: list[str], c_file: str, linker_script: str) -> bool:
    args = ['rtems-ldep', '-f']
    if c_file is not None:
        args += ['-C', c_file]
    if linker_script is not None:
        args += ['-e', linker_script]
    args += nm_files
    r = subprocess.run(
        args
    )
    return r.returncode == 0

def main():
    args = parser.parse_args()
    
    COMPILER = _get_tool_name(args.C, 'g++')
    NM = _get_tool_name(args.C, 'nm')
    READELF = _get_tool_name(args.C, 'readelf')

    if args.v:
        print(_get_compiler_lib_paths(_get_tool_name(args.C, 'g++')))

    libsyms = {}
    base_syms = set()

    LIBDIRS = [] if args.L is None else args.L
    LIBS = [] if args.l is None else args.l
    
    LIBDIRS += _get_compiler_lib_paths(COMPILER)

    # Generate list of symbols from libraries and base image
    nm_files = _gen_symbols_for_libs(NM, args.O, LIBS, LIBDIRS)
    if nm_files is None:
        exit(-1)

    # Run ldep
    if not _run_ldep(nm_files, args.c, args.e):
        exit(-1)

if __name__ == '__main__':
    main()
