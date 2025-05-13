#
# Additional tools for rtems_waf
#

import rtems_waf.rtems as rtems

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