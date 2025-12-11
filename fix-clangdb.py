#!/usr/bin/env python3
# ----------------------------------------------------------------------------
# Company    : SLAC National Accelerator Laboratory
# ----------------------------------------------------------------------------
# Description : Fix a compile_commands.json so that it plays nice with clangd
# Does the following:
#  - removes arguments that clangd cannot understand (i.e. -qrtems)
#  - Adds -I for each -B search path
#  - Adds built-in compiler include paths to the command line
# ----------------------------------------------------------------------------
# This file is part of the rtems-tools package. It is subject to
# the license terms in the LICENSE.txt file found in the top-level directory
# of this distribution and at:
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
# No part of the rtems-tools package, including this file, may be
# copied, modified, propagated, or distributed except according to the terms
# contained in the LICENSE.txt file.
# ----------------------------------------------------------------------------

import json
import argparse
import subprocess
import shlex

def get_compiler_include_paths(compiler: str) -> list[str]:
    """
    Returns a list of compiler built-in include paths
    """
    r = subprocess.run([compiler, '-E', '-Wp,-v', '-xc', '/dev/null'], capture_output=True)
    o = r.stderr.decode('utf-8').split('\n')
    out = []
    for l in o:
        if l.startswith(' '):
            out.append('-I' + l.removeprefix(' '))
    return out

def clean_arg(arg: str) -> str:
    return arg.removeprefix('\\')

# clangd can't understand these.
REMOVE_ARGS = [
    '-qrtems',
    '-specs',
    'bsp_specs',
    '-mpreferred-stack-boundary=3',
    '-mindirect-branch=thunk-extern',
    '-mindirect-branch-register',
    '-fno-allow-store-data-races',
    '-fconserve-stack',
    '-mrecord-mcount',
    '-fsanitize=bounds-strict',
    '-mindirect-branch-cs-prefix',
    '-mfunction-return=thunk-extern',
    '-fzero-call-used-regs=used-gpr',
    '-ftrivial-auto-var-init=zero',
    '-mcpu=5282' # clang only supports a few 68k CPUs
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='FILE', type=str, required=True)
    parser.add_argument('-i', dest='INCLUDES', nargs='+', help='Add these directories as include paths')
    parser.add_argument('-s', dest='FLAGS', nargs='+', help='Add these flags')
    parser.add_argument('-c', type=str, dest='COMPILER', help='Set the compiler to this')
    parser.add_argument('-r', dest='REMOVE', nargs='+', help='Args to remove')
    args = parser.parse_args()

    j = {}
    with open(args.FILE, 'r') as fp:
        j = json.load(fp)

    # If in command syntax mode, convert to arguments
    for f in j:
        if 'command' in f and 'arguments' not in f:
            f['arguments'] = shlex.split(f['command'])

    for f in j:
        for toremove in REMOVE_ARGS:
            try:
                f['arguments'].remove(toremove)
            except:
                pass

        if args.COMPILER is not None:
            f['arguments'][0] = args.COMPILER

        for a in f['arguments']:
            if a.startswith('-B'):
                f['arguments'].append(a.replace('-B', '-I') + '/include')
                break
        if args.INCLUDES is None:
            args.INCLUDES = []
        f['arguments'] += ['-I' + x for x in args.INCLUDES]
        f['arguments'] += get_compiler_include_paths(f['arguments'][0])
        if args.FLAGS is not None:
            f['arguments'] += [clean_arg(x) for x in args.FLAGS]


    with open(args.FILE, 'w') as fp:
        json.dump(j, fp, indent=2)


if __name__ == '__main__':
    main()

# vim: et sw=4 ts=4