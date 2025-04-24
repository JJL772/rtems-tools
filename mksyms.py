#!/usr/bin/env python3
#===========================================================================#
# SYNOPSIS: mksyms.py
#===========================================================================#
# Utility to build a "diff list" of symbols present in linked libraries that 
# aren't present in the base image. This diff list is then turned into a C
# file that cross references the symbols so it can be linked into a new base
# image. 
# We want to create a "super" image for dynamic linking using the RTEMS RTL,
# so that libraries like librtemsbsp.a, librtemscpu.a, etc. don't need to be
# present on the file system at object load time. Due to linker elison, 
# symbols from static libs are usually excluded unless a symbol in its 
# object file is directly referenced. These references can be done on the
# command line using -u, or it can be done like it is here.

import argparse
import os
import sys
import tempfile
import subprocess
import regex
import configparser

parser = argparse.ArgumentParser()
parser.add_argument('-l', action='append', help='Library to search in')
parser.add_argument('-L', action='append', help='Additional library search paths')
parser.add_argument('-f', type=str, help='Base image')
parser.add_argument('-m', type=str, help='Difference mapping')
parser.add_argument('-v', action='store_true', help='Verbose')
parser.add_argument('-C', type=str, default='', help='Compiler prefix (i.e. powerpc-rtems6 for powerpc-rtems6-gcc)')
parser.add_argument('-o', type=str, required=True, help='Output C source file')
parser.add_argument('-g', type=str, help='File containing a list of exclude filters')
parser.add_argument('-r', type=str, help='List of additional symbols to reference')

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

def _get_syms(cmd: str, file: str) -> set[str]:
    """
    Obtains a set of symbols from the file using nm
    """
    r = subprocess.run([cmd, '-fjust-symbols', '-U', file], capture_output=True, universal_newlines=True)
    if r.returncode != 0:
        raise RuntimeError(f'Error while reading {file}: {r.stdout}')
    return set(r.stdout.splitlines())

def _find_lib(paths: list[str], lib: str) -> str | None:
    """
    Tries to find a library based on the provided library search paths
    """
    for p in paths:
        if os.path.exists(f'{p}/lib{lib}.a'):
            return f'{p}/lib{lib}.a'
    return None

def _gen_refs(file: str, syms: set):
    """
    Generate a C source file that contains a huge list of symbol refs
    """
    with open(file, 'w') as fp:
        fp.write('/** WARNING: Generated symbol ref file, do not edit! **/\n\n')
        num = 0
        for sym in syms:
            fp.write(f'asm(".set __symref_alias_{num},{sym}\\n");\n')
            fp.write(f'extern void* __symref_alias_{num};\n')
            num += 1
        fp.write('void __symbolRefDummy() {static int n = 0; n++;\n')
        num = 0
        for sym in syms:
            # This is getting annoying. GCC is WAYYYYYYYYYYY TOO aggressive with the symbol removal.
            # Like seriously. I'm *telling you* to emit a reference, very explicitly. Please do it!
            # Do you really expect me to add --undefine ... on the command line for EVERY symbol??? really?
            fp.write(f'__symref_alias_{num} = (n % 2) ? __symref_alias_{num} : 0;\n')
            num += 1
        fp.write('\n}')

def _load_list_file(file: str) -> set[str]:
    """
    Load a list of filtered out symbols from a file
    """
    s = set()
    with open(file, 'r') as fp:
        lines = fp.readlines()
        for l in lines:
            l = l.strip()
            if len(l) > 0 and not l.startswith('#'):
                s.add(l)
    return s
        

def main():
    args = parser.parse_args()
    
    COMPILER = _get_tool_name(args.C, 'g++')
    NM = _get_tool_name(args.C, 'nm')

    if args.v:
        print(_get_compiler_lib_paths(_get_tool_name(args.C, 'g++')))

    filters = set()
    if args.g is not None:
        filters = _load_list_file(args.g)
    
    extra = set()
    if args.r is not None:
        extra = _load_list_file(args.r)

    libsyms = {}
    base_syms = set()

    LIBDIRS = [] if args.L is None else args.L
    LIBS = [] if args.l is None else args.l
    
    LIBDIRS += _get_compiler_lib_paths(COMPILER)

    # Generate base image symbols
    if args.f is not None:
        base_syms = _get_syms(NM, args.f)

    # Generate list of library symbols
    for a in LIBS:
        l = _find_lib(LIBDIRS, a)
        if l is None:
            print(f'Failed to find -l{a}')
            exit(1)
        libsyms[a] = _get_syms(NM, l)

    diff_syms = set()

    # Diff the sets
    for k,v in libsyms.items():
        diff_syms = diff_syms.union(v.difference(base_syms))

    # Diff with filters
    diff_syms = diff_syms.difference(filters)
    
    # Add in extra cross ref'ed symbols
    diff_syms = diff_syms.union(extra)

    # Generate a list of dummy symbol refs
    _gen_refs(args.o, diff_syms)

    if args.v:
        print(diff_syms)

if __name__ == '__main__':
    main()