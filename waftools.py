# ----------------------------------------------------------------------------
# Company    : SLAC National Accelerator Laboratory
# ----------------------------------------------------------------------------
# Description : Tools for RTEMS waf
# ----------------------------------------------------------------------------
# This file is part of the rtems-tools package. It is subject to
# the license terms in the LICENSE.txt file found in the top-level directory
# of this distribution and at:
#    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html.
# No part of the rtems-tools package, including this file, may be
# copied, modified, propagated, or distributed except according to the terms
# contained in the LICENSE.txt file.
# ----------------------------------------------------------------------------

import rtems_waf.rtems as rtems
from waflib.Task import Task
from waflib import Context
from waflib.TaskGen import feature, extension
import waflib.TaskGen as Taskgen
import waflib
import os
import sys
import tools.findlibs as findlibs

# HACK! I still want mkrootfs to run w/o a real package.
sys.path.append(os.path.dirname(__file__))
import mkrootfs

rtems_version = "7"

def get_install_prefix(ctx) -> str:
    """
    Returns the install prefix for the specified BSP and arch

    Parameters
    ----------
    ctx :
        Build context
    """
    return f'${{PREFIX}}/{ctx.options.SSRLAPPS_VER}/{ctx.env.RTEMS_ARCH_RTEMS}/{ctx.env.RTEMS_BSP}'

def get_lib_paths(ctx) -> list[str]:
    """
    Returns a list of library search directories for the specified bsp

    Parameters
    ----------
    ctx :
        Build context
    """
    return [
        f'{ctx.env.RTEMS_PATH}/{rtems.arch_bsp_lib_path(rtems_version, ctx.env.RTEMS_ARCH_BSP)}',
        f'{ctx.env.RTEMS_PATH}/{ctx.options.SSRLAPPS_VER}/{rtems.arch_bsp_lib_path(rtems_version, ctx.env.RTEMS_ARCH_BSP)}'
    ]

def get_includes(ctx) -> list[str]:
    """
    Returns a list of include directories

    Parameters
    ----------
    ctx :
        Build context
    """
    return [
        f'{ctx.env.RTEMS_PATH}/{rtems.arch_bsp_include_path(rtems_version, ctx.env.RTEMS_ARCH_BSP)}',
        '.'
    ]

def install_headers(bld, headers: list[str], subdir: str = ''):
    """
    Installs some headers

    Parameters
    ----------
    bld :
        Build context
    headers : list[str]
        List of heaaders to install
    subdir : str
        Subdirectory within the include directory
    """
    bld.install_files(
        f'{get_install_prefix(bld)}/include/{subdir}',
        headers
    )

def install_libs(bld, libs: list[str], subdir: str = ''):
    """
    Installs some libraries

    Parameters
    ----------
    bld :
        Build context
    libs : list[str]
        List of libs to install
    subdir : str
        Subdirectory within the include directory
    """
    bld.install_files(
        f'{get_install_prefix(bld)}/lib/{subdir}',
        libs
    )


def build_module(bld, target: str, sources: list[str] = [], includes: list[str] = [], ldflags: list[str] = [], libs: list[str] = []):
    """
    Builds the specified module with the specified properties.
    Does not link to the standard library or any other RTEMS libraries by default

    Parameters
    ----------
    bld :
        Build context
    target : str
        Name of the target file to generate
    sources : list[str]
        Source files to compile
    includes : list[str]
        Include directories to append
    ldflags : list[str]
        Linker flags to append
    libs : list[str]
        Libraries to link against
    """

    includes = includes.copy()
    includes.extend(get_includes(bld))

    def link_task(task):
        cmd = [
            bld.env.CC[0],
            '-o',
            task.outputs[0].abspath(),
            '-nostdlib',
            '-Wl,-r',
        ]
        cmd.extend(bld.env.CFLAGS)
        cmd.extend(bld.env.CPPFLAGS)
        cmd.extend([f'-L{x}' for x in get_lib_paths(bld)])
        # Relative to build dir
        cmd.extend([bld.env.CPPPATH_ST % x for x in task.generator.includes])
        # Relative to srcdir
        cmd.extend([bld.env.CPPPATH_ST % f'{bld.top_dir}/{x}' for x in task.generator.includes])
        cmd.extend(task.generator.ldflags)
        cmd.extend([x.abspath() for x in task.inputs])
        cmd.extend(task.generator.libs)
        print(' '.join(cmd))
        return task.exec_command(cmd)

    bld(
        rule=link_task,
        source=[sources],
        includes=includes,
        libs=libs,
        ldflags=ldflags,
        target=target
    )

    # Install to rtems bsp subdir
    bld.install_files(f'{get_install_prefix(bld)}/bin', target)

def check_headers(conf, headers: dict, allow_failure: bool = True):
    """
    Checks for a list of headers and generates a define for them

    Parameters
    ----------
    conf :
        Config context
    headers : dict
        Mapping of header -> define
    allow_failure : bool
        Allow failure of the check or not
    """
    for k, v in headers.items():
        try:
            conf.check_cc(
                use='rtemsdefaultconfig',
                header_name=k,
                features='c',
                define_name=v
            )
        except Exception as e:
            if not allow_failure:
                raise e


def has_c_header(conf, header: str) -> bool:
    """
    Checks for a specific header and returns true if it's found

    Parameters
    ----------
    conf :
        Config context
    header : str
        Build context
    
    Returns
    -------
    True if the header is found, false otherwise
    """
    try:
        conf.check_cc(
            use='rtemsdefaultconfig',
            header_name=header,
            features='c'
        )
    except:
        return False
    return True

def has_lib(conf, libs: list[str]) -> bool:
    """
    Checks for a specific library

    Parameters
    ----------
    conf :
        Config context
    lib : list[str]
        Name of the library
    """
    try:
        conf.check_cc(
            use=libs + ['rtemsdefaultconfig'],
            features='cprogram',
            msg=f'Checking for {" ".join(libs)}'
        )
    except:
        return False
    return True

def add_rootfs(bld, dir: str, file: str = 'rootfs.S', macros: dict = {}, tarball: bool = True):
    """
    Adds a directory as the rootfs. This directory should contain a rootfs.txt file
    describing the files to be installed, their destination, permissions, ownership, etc.

    Operates in two modes: tarball and custom. 'Custom' mode effectively embeds each
    file individually and generates the code needed to write them out with proper permissions.
    Tarball does what it says on the tin. Intended to be used with RTEMS's built-in tarfs
    system.
    
    This will generate a source file with the embedded data.

    Parameters
    ----------
    bld :
        Build context
    dir : str
        Directory that contains the rootfs.txt
    file : str
        Name of the generated file
    macros : dict
        Dict defining macros and their corresponding values. rootfs.txt will be processed with
        these using string.Template
    tarball : bool
        When true, generate an embedded tarball, otherwise use the other method
    """
    
    def generate(task):
        bld.to_log(f'Generating {file}\n')
        if tarball:
            mkrootfs.generate_tarball(
                os.path.dirname(task.inputs[0].abspath()),
                task.outputs[0].abspath(),
                macros
            )
        else:
            mkrootfs.generate_source(
                os.path.dirname(task.inputs[0].abspath()),
                task.outputs[0].abspath(),
                macros
            )

    return bld(
        name=f'{bld.out_dir}/{bld.env.RTEMS_ARCH_BSP}/{file}',
        target=f'{bld.out_dir}/{bld.env.RTEMS_ARCH_BSP}/{file}',
        source=[f'{dir}/rootfs.txt'],
        rule=generate
    )


def check_include(conf, include: str, var: str, system: bool = False, add_to_defines: bool = True) -> bool:
    """
    Performs a compile-time check for the include.
    
    Parameters
    ----------
    conf :
        Configuration context
    include : str
        Include to try
    var : str
        Variable to set
    system : bool
        When true, include with arrow brackets
    add_to_defines: bool
        When true, add to the list of C/C++ #defines
    
    Returns
    -------
    bool :
        Boolean indicating whether the include was found or not.
    """
    
    if system:
        code = [f'#include <{include}>']
    else:
        code = [f'#include "{include}"']

    try:
        conf.check_cc(
            fragment=rtems.test_application(code),
            execute=False,
            msg='Checking for %s' % (include)
        )
    except conf.errors.WafError:
        setattr(conf.env, var, False)
        return False

    if add_to_defines:
        conf.env.DEFINES += [f'{var}=1']
    setattr(conf.env, var, True)
    return True


def write_config_h(conf, template: str, name: str | None = None):
    """
    Writes out a config.h header in the build area for this arch/bsp
    
    Parameters
    ----------
    conf :
        Configuration context
    template : str
        Template file to substitute
    name : str | None
        Name of the config.h file. If None, it is determined by stripping the .in suffix from template.
    """
    with open(template, 'r') as fp:
        tpl = fp.read()
    
    if name is None:
        name = os.path.basename(template).removesuffix('.in')

    for k in conf.env:
        v = getattr(conf.env, k)
        if type(v) in [int, float]:
            tpl = tpl.replace(f'@{k}@', str(v))
        elif type(v) == bool:
            tpl = tpl.replace(f'@{k}@', str(1 if v else 0))
        else:
            tpl = tpl.replace(f'@{k}@', f'"str(v)"')

    os.makedirs(f'{conf.bldnode.abspath()}/{conf.env.RTEMS_ARCH_BSP}/', exist_ok=True, mode=0o777)
    with open(f'{conf.bldnode.abspath()}/{conf.env.RTEMS_ARCH_BSP}/{name}', 'w') as fp:
        fp.write(tpl)


def check_net_stack(conf, lib: str, name: str):
    """
    Determines the networking stack this BSP is configured for.
    
    Parameters
    ----------
    lib : str
        The actual library to check for (lwip, networking, bsd)
    name : str
        The name of the networking stack (lwip, legacy, bsd)
    """

    # This is derived from the check in rtems-net-services:
    conf.check_cc(
        lib=lib,
        ldflags=['-lrtemsdefaultconfig'],
        uselib_store=f'NET_{name.upper()}',
        mandatory=False
    )
    if f'LIB_NET_{name.upper()}' in conf.env:
        conf.env.NET_NAME = name
        # clean up the check
        conf.env[f'LDFLAGS_NET_{name}'] = []
        conf.env[f'LIB_NET_{name}'] += ['m']
        return True
    return False


def check_lib(conf, lib: str, symbol: str, variable: str) -> bool:
    """
    Performs a "library check", searching for 'symbol' in 'lib' and setting
    a variable on the environment to indicate if it's found.
    
    Parameters
    ----------
    lib : str
        Library name (without lib prefix or path)
    symbol : str
        Name of the symbol
    variable : str
        Name of the variable to set in conf.env
    """
    # Default to false
    conf.env[variable] = False

    # Find the library file itself
    args = [f'-B{conf.env.RTEMS_PATH}/{conf.env.RTEMS_ARCH_RTEMS}/{conf.env.RTEMS_BSP}']
    l = findlibs.find_lib(
        conf.env.CC[0],
        findlibs.make_lib_name(lib),
        args,
    )

    if l is None:
        conf.msg(f'Checking for {symbol} in {lib}', 'no', 'YELLOW')
        return False

    found = findlibs.check_sym(l, symbol, conf.env.NM[0])
    conf.msg(f'Checking for {symbol} in {lib}', 'no' if not found else 'yes', 'GREEN' if found else 'YELLOW')
    conf.env[variable] = True
    return found

def report_feature(ctx, feature: str, enabled: bool, msg: tuple[str, str] = ('enabled', 'disabled')):
    """Reports a feature as enabled/disabled"""
    ctx.msg(
        feature,
        msg[0] if enabled else msg[1],
        'GREEN' if enabled else 'YELLOW'
    )

"""
Generates a flat binary with the file extension .boot
If your app's name is 'my-app.exe', it will generate a 'my-app.boot' for you.

Simply add to your app's 'features' list
"""
@feature('boot')
@Taskgen.after('process_use')
def generate_boot_file(self):
    path = f"{self.bld.out_dir}/{self.env.RTEMS_ARCH_BSP}/{self.target}"
    out = os.path.splitext(path)[0] + '.boot'

    class bootTask(Task):
        color = 'YELLOW'

        def __init__(self, *args, **kws):
            super().__init__(*args, **kws)
            # Always run after the linker task...
            self.run_after.add(self.generator.link_task)

        def run(self):
            return 0 != self.exec_command(
                f"{self.env.OBJCOPY[0]} -O binary {path} {out}"
            )

        def __str__(self):
            return f'Generating {os.path.basename(out)}'

    t = self.create_task('bootTask')
