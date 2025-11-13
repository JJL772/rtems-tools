#!/usr/bin/env python3
#===========================================================================#
# SYNOPSIS: findlibs.py
#===========================================================================#
# Finds libraries in built-in compiler library paths, and explicit dirs
# specified by -L
# Can also be used to check for the existance of a symbol in one of the libs
import subprocess
import argparse
import os
import sys

parser = argparse.ArgumentParser()
parser.add_argument('-l', required=True, action='append', help='Library')
parser.add_argument('-L', action='append', help='Library directory')
parser.add_argument('-C', required=True, type=str, help='Compiler binary')
parser.add_argument('--check-sym', type=str, dest='SYM', help='Check libraries for this symbol')

def _find_lib(compiler: str, lib: str, args: list[str]) -> str | None:
    """
    Prints library file name using gcc. It's behavior is a bit funny; lookup failures just yield the same string you passed in.
    It also needs a fully qualified library name (libblah.a).
    """
    r = subprocess.run([compiler, f'-print-file-name={lib}'] + args, capture_output=True, universal_newlines=True)
    if r.returncode != 0 or lib == r.stdout.strip():
        return None
    return r.stdout.strip()

def _check_sym(lib: str, sym: str) -> bool:
    """
    Checks if a symbol can be found in the specified library using nm
    """
    r = subprocess.run(['nm', '-jU', lib], capture_output=True, universal_newlines=True)
    if r.returncode != 0:
        print(f'NM failed with {r.stderr}')
        return False
    return sym in r.stdout.splitlines()

def _make_lib_name(lib: str) -> str:
    return f'lib{lib}.a'

def main():
    args, cargs = parser.parse_known_args()

    # Resolve libs
    libs = []
    for lib in args.l:
        r = _find_lib(args.C, _make_lib_name(lib), cargs)
        if r is None:
            print(f'Could not find -l{lib}')
            exit(1)
        libs.append(r)

    # Check for symbols if in check-syms mode
    if args.SYM:
        if not any([_check_sym(lib, args.SYM) for lib in libs]):
            print(f'{args.SYM} not found in any of: {",".join(args.l)}')
            exit(1)
    else:
        [print(l) for l in libs]

    exit(0)

if __name__ == '__main__':
    # This is a pretty awful workaround for a CMake limitation... execute_process does not do any shell tokenizing
    # of commands, and CMAKE_C_FLAGS usually ends up interpreted as a string
    # To workaround this, we'll have to check for and remove the --cmake option, and re-launch ourselves using subprocess
    if '--cmake' in sys.argv:
        args = sys.argv
        args.remove('--cmake')
        exit(subprocess.run(" ".join(args), shell=True).returncode)

    main()