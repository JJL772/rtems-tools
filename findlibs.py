#!/usr/bin/env python3

import subprocess
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument('-l', required=True, action='append', help='Library')
parser.add_argument('-L', action='append', help='Library directory')
parser.add_argument('-C', required=True, type=str, help='Compiler binary')

def _get_compiler_lib_paths(compiler: str, args: list[str]) -> list[str]:
    """
    Returns a list of compiler library search paths
    """
    r = subprocess.run([compiler, '-print-search-dirs'] + args, capture_output=True, universal_newlines=True)
    if r.returncode != 0:
        return []
    lines = [x for x in r.stdout.splitlines() if x.startswith('libraries:')]
    return [x.removeprefix(' =') for x in lines[0].split(':') if x != 'libraries']


def _find_lib(lib: str, paths: list[str]) -> str | None:
    for p in paths:
        p = p.removesuffix('/')
        tocheck = [
            f'{p}/lib{lib}.a',
            f'{p}/{lib}.a',
            f'{p}/{lib}',
        ]
        for c in tocheck:
            if os.path.exists(c):
                return c
    return None

def main():
    args, cargs = parser.parse_known_args()

    paths = _get_compiler_lib_paths(args.C, cargs)
    if args.L is not None:
        paths += args.L
    
    for l in args.l:
        print(_find_lib(l, paths))


if __name__ == '__main__':
    main()