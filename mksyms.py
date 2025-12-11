#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Company    : SLAC National Accelerator Laboratory
# ----------------------------------------------------------------------------
# Description : Utility to build a "diff list" of symbols present in linked 
# libraries that  aren't present in the base image. This diff list is then
# turned into a C file that cross references the symbols so it can be linked
# into a new base image. 
# We want to create a "super" image for dynamic linking using the RTEMS RTL,
# so that libraries like librtemsbsp.a, librtemscpu.a, etc. don't need to be
# present on the file system at object load time. Due to linker elison,
# symbols from static libs are usually excluded unless a symbol in its
# object file is directly referenced. These references can be done on the
# command line using -u, or it can be done like it is here.
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
import tomllib
import re

parser = argparse.ArgumentParser()
parser.add_argument('-l', metavar='lib', action='append', help='Library to search in')
parser.add_argument('-L', metavar='dir', action='append', help='Additional library search paths')
parser.add_argument('-f', metavar='file', type=str, help='Base image')
parser.add_argument('-m', metavar='file', type=str, help='Difference mapping')
parser.add_argument('-v', action='store_true', help='Verbose')
parser.add_argument('-C', type=str, metavar='prefix', default='', help='Compiler prefix (i.e. powerpc-rtems6 for powerpc-rtems6-gcc)')
parser.add_argument('-o', type=str, metavar='file', required=True, help='Output file')
parser.add_argument('-T', choices=['c', 'linker'], default='c', help='Output type, either C or linker script')
parser.add_argument('-g', type=str, metavar='file', nargs='+', help='File containing a list of exclude filters')
parser.add_argument('-r', type=str, metavar='syms', help='List of additional symbols to reference')
parser.add_argument('-N', type=str, metavar='name', default='__symbolRefDummy', help='Name of the function to output, defaults to __symbolRefDummy')
parser.add_argument('-a', type=str, metavar='ARCH', required=True, help='Target architecture')
parser.add_argument('-c', type=str, metavar='CONFIG', help='Path to a toml file to be used as a symbol config')
parser.add_argument('--tls', action='store_true', help='Keep TLS symbols')

# Default symbols to skip
DEFAULT_FILTERS = set([
    'GNU-stack'
])

def _parse_config(f: str, arch: str) -> tuple[set, set, set]:
    """
    Parses a symbol config in toml

    Parameters
    ----------
    f : str
        Name of the file to parse
    arch : str
        Target architecture

    Returns
    -------
    tuple[list,list]
        List of (refs, excludes, exclude_files)
    """
    cfg = {}
    with open(f, 'rb') as fp:
        cfg = tomllib.load(fp)

    excludes = []
    refs = []
    exclude_files = []

    def parse_section(cfg: dict) -> tuple[list, list, list]:
        refs = []
        excludes = []
        exclude_files = []
        if 'exclude' in cfg: excludes += cfg['exclude']
        if 'ref' in cfg: refs += cfg['ref']
        if 'exclude_files' in cfg: exclude_files += cfg['exclude_files']
        return (refs, excludes, exclude_files)

    if 'symbols' in cfg:
        r, e, ef = parse_section(cfg['symbols'])
        refs += r
        excludes += e
        exclude_files += ef
        if arch in cfg['symbols']:
            r, e, ef = parse_section(cfg['symbols'][arch])
            refs += r
            excludes += e
            exclude_files += ef

    return (set(refs), set(excludes), set(exclude_files))

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

def _determine_file(l: str) -> str:
    """
    Parses object file out of a string in the format /path/to/lib.a(something.o)
    """
    m = re.match(r'\S+\((\S+)\)', l)
    try:
        return m.group(1)
    except:
        return ''

def _get_syms_readelf(cmd: str, file: str, ignored_files: list[str], skip_tls: bool = True) -> set[str]:
    """
    Obtains a set of symbols from the file using readelf

    Parameters
    ----------
    cmd : str
        readelf command to run
    file : str
        
    """
    r = subprocess.run([cmd, '-s', '-W', file], capture_output=True, universal_newlines=True)
    if r.returncode != 0:
        raise RuntimeError(f'Error while reading {file}: {r.stdout}')
    lines = r.stdout.splitlines()
    result = set()
    file = ''
    for l in lines:
        # columns: num addr size type bind visibility ndx name (we only care about name and type)
        cols = l.split()
        # Determine file
        if len(cols) == 2 and cols[0] == 'File:':
            file = _determine_file(cols[1])
            continue
        # Check if file is ignored
        if file in ignored_files:
            continue
        if len(cols) != 8: continue
        # Skip tls symbols if requested
        if cols[3] == 'TLS' and skip_tls: continue
        # Skip sections, files
        if cols[3] in ['SECTION', 'FILE']: continue
        # Skip non-global or weak symbols
        if cols[4] not in ['GLOBAL', 'WEAK']: continue
        # Skip hidden symbols
        if cols[5] != 'DEFAULT': continue
        # Skip undefined
        if cols[6] == 'UND': continue
        result.add(cols[7])
    return result

def _find_lib(paths: list[str], lib: str) -> str | None:
    """
    Tries to find a library based on the provided library search paths
    """
    for p in paths:
        if os.path.exists(f'{p}/lib{lib}.a'):
            return f'{p}/lib{lib}.a'
    return None

def _gen_refs_lds(file: str, syms: set) -> bool:
    """
    Generate a linker script with a bunch of EXTERN() directives
    """
    with open(file, 'w') as fp:
        for s in syms:
            fp.write(f'EXTERN({s})\n')
    return True

def _gen_refs_c(funcname: str, file: str, syms: set):
    """
    Generate a C source file that contains a huge list of symbol refs
    """
    with open(file, 'w') as fp:
        fp.write(
f"""
/**
 * WARNING: Generated file! Do not edit!
 * Generated with '{" ".join(sys.argv)}'
 */
"""
        )
        num = 0
        for sym in syms:
            fp.write(f'asm(".set __symref_alias_{num},{sym}\\n");\n')
            fp.write(f'extern void* __symref_alias_{num};\n')
            num += 1
        fp.write('\n#pragma GCC push_options\n#pragma GCC optimize("O0")\n')
        fp.write(f'void __attribute__((used)) {funcname}() {{\n')
        num = 0
        for sym in syms:
            fp.write(f'__symref_alias_{num} = __symref_alias_{num};\n')
            num += 1
        fp.write('}\n')
        fp.write('#pragma GCC pop_options\n')

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
    keep_tls = True if args.tls else False

    COMPILER = _get_tool_name(args.C, 'g++')
    NM = _get_tool_name(args.C, 'nm')
    READELF = _get_tool_name(args.C, 'readelf')

    if args.v:
        print(_get_compiler_lib_paths(_get_tool_name(args.C, 'g++')))

    # Gather list of filters
    filters = DEFAULT_FILTERS
    if args.g is not None:
        for file in args.g:
            filters = filters.union(_load_list_file(file))
    print(filters)

    # Gather list of additional symbol refs
    extra = set()
    if args.r is not None:
        extra = _load_list_file(args.r)

    # Load config if provided
    ignored_files = set()
    if args.c is not None:
        e, f, ef = _parse_config(args.c, args.a)
        extra.update(e)
        filters.update(f)
        ignored_files.update(ef)
    print(f'Extra refs: {extra}')
    print(f'Filters: {filters}')
    print(f'Ignored Files: {ignored_files}')

    libsyms = {}
    base_syms = set()

    LIBDIRS = [] if args.L is None else args.L
    LIBS = [] if args.l is None else args.l

    LIBDIRS += _get_compiler_lib_paths(COMPILER)

    # Generate base image symbols
    if args.f is not None:
        base_syms = _get_syms_readelf(READELF, args.f, ignored_files, keep_tls)

    # Generate list of library symbols
    for a in LIBS:
        l = _find_lib(LIBDIRS, a)
        if l is None:
            print(f'Failed to find -l{a}')
            exit(1)
        libsyms[a] = _get_syms_readelf(READELF, l, ignored_files, keep_tls)

    diff_syms = set()

    # Diff the sets
    for k,v in libsyms.items():
        diff_syms = diff_syms.union(v.difference(base_syms))

    # Diff with filters
    diff_syms = diff_syms.difference(filters)
    for f in filters:
        assert f not in diff_syms
        assert f not in extra
    
    # Add in extra cross ref'ed symbols
    diff_syms = diff_syms.union(extra)

    # Generate a list of dummy symbol refs
    if args.T == 'linker': 
        _gen_refs_lds(args.o, diff_syms)
    elif args.T == 'c':
        _gen_refs_c(args.N, args.o, diff_syms)

    if args.v:
        print(diff_syms)

if __name__ == '__main__':
    main()
