set(CMAKE_SYSTEM_NAME "RTEMS")
set(CMAKE_SYSTEM_PROCESSOR "${RTEMS_ARCH}")

set(CMAKE_CROSSCOMPILING ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if (NOT DEFINED RTEMS_VERSION)
    message(WARNING "RTEMS_VERSION not set, defaulting to 6.0")
    set(RTEMS_VERSION 6.0)
endif()

# Break up RTEMS_VERSION into chunks
string(REGEX MATCH "([0-9]+)\.([0-9]+)\.?([0-9]+)?" RTEMS_FULL_VERSION "${RTEMS_VERSION}")
set(RTEMS_MAJOR "${CMAKE_MATCH_1}")
set(RTEMS_MINOR "${CMAKE_MATCH_2}")
set(RTEMS_PATCH "${CMAKE_MATCH_3}")

# RTEMS 4.X doesn't use a version prefix on the tool, i.e. powerpc-rtems-gcc instead of powerpc-rtems6-gcc
if (NOT DEFINED RTEMS_TOOL_VERSION AND NOT "${RTEMS_MAJOR}" STREQUAL "4")
    set(RTEMS_TOOL_VERSION "${RTEMS_MAJOR}")
endif()

if (NOT DEFINED RTEMS_ARCH)
    message(FATAL_ERROR "RTEMS_ARCH must be provided by the including toolchain file")
endif()

#
# Compiler configuration
#
set(CMAKE_C_COMPILER "${RTEMS_ARCH}-rtems${RTEMS_TOOL_VERSION}-gcc")
set(CMAKE_CXX_COMPILER "${RTEMS_ARCH}-rtems${RTEMS_TOOL_VERSION}-g++")
set(CMAKE_ASM_COMPILER "${RTEMS_ARCH}-rtems${RTEMS_TOOL_VERSION}-gcc")
set(CMAKE_LINKER "${RTEMS_ARCH}-rtems${RTEMS_TOOL_VERSION}-ld")
set(CMAKE_AR "${RTEMS_ARCH}-rtems${RTEMS_TOOL_VERSION}-ar")
set(CMAKE_OBJCOPY "${RTEMS_ARCH}-rtems${RTEMS_TOOL_VERSION}-objcopy")
set(CMAKE_RTEMS_LD "rtems-ld")
set(CMAKE_RTEMS_XSYMS "rtems-xsyms")
set(CMAKE_RTEMS_SYMS "rtems-syms")
set(CMAKE_DTC "dtc")
if (DEFINED RTEMS_TOP)
    if (NOT DEFINED HOST_DIR)
        if (EXISTS "${RTEMS_TOP}/host/linux-x86_64")
            set(HOST_DIR "linux-x86_64")
        elseif (EXISTS "${RTEMS_TOP}/host/amd64_linux26")
            set(HOST_DIR "amd64_linux26")
        else()
            message(FATAL_ERROR "Unable to determine HOST_DIR")
        endif()
    endif()

    set(CMAKE_C_COMPILER "${RTEMS_TOP}/host/${HOST_DIR}/bin/${CMAKE_C_COMPILER}")
    set(CMAKE_CXX_COMPILER "${RTEMS_TOP}/host/${HOST_DIR}/bin/${CMAKE_CXX_COMPILER}")
    set(CMAKE_ASM_COMPILER "${RTEMS_TOP}/host/${HOST_DIR}/bin/${CMAKE_ASM_COMPILER}")
    set(CMAKE_LINKER "${RTEMS_TOP}/host/${HOST_DIR}/bin/${CMAKE_LINKER}")
    set(CMAKE_AR "${RTEMS_TOP}/host/${HOST_DIR}/bin/${CMAKE_AR}")
    set(CMAKE_OBJCOPY "${RTEMS_TOP}/host/${HOST_DIR}/bin/${CMAKE_OBJCOPY}")
    set(CMAKE_RTEMS_SYMS "${RTEMS_TOP}/host/${HOST_DIR}/bin/rtems-syms")
    set(CMAKE_RTEMS_LD "${RTEMS_TOP}/host/${HOST_DIR}/bin/rtems-ld")
    set(CMAKE_RTEMS_XSYMS "${RTEMS_TOP}/host/${HOST_DIR}/bin/rtems-xsyms")
    set(CMAKE_DTC "${RTEMS_TOP}/host/${HOST_DIR}/bin/dtc")
endif()

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

# When testing ${CMAKE_C[XX]_COMPILER} functionality, don't try to link a test application
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

# May be set by individual toolchain files
if (NOT DEFINED RTEMS_SUBDIR)
    set(RTEMS_SUBDIR "rtems")
endif()

#
# Misc definitions
#
set(RTEMS_VER "${RTEMS_VERSION}")
set(RTEMS_BSP_DIR "${RTEMS_TOP}/target/${RTEMS_SUBDIR}/${RTEMS_ARCH}-rtems${RTEMS_TOOL_VERSION}/${RTEMS_BSP}")
set(RTEMS_BSP_HOST_DIR "${RTEMS_TOP}/host/${HOST_DIR}/${RTEMS_ARCH}-rtems${RTEMS_TOOL_VERSION}")

#
# Install prefix
#
if (DEFINED RTEMS_INSTALL_TOP)
    set(CMAKE_INSTALL_PREFIX "${RTEMS_INSTALL_TOP}/target/${RTEMS_SUBDIR}/${RTEMS_ARCH}-rtems${RTEMS_TOOL_VERSION}/${RTEMS_BSP}")
    message("CMAKE_INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX}")
endif()

#
# BSP specific compiler flags
#
set(RTEMS_BSP_INCDIR "${RTEMS_BSP_DIR}/lib/include")
set(RTEMS_CFLAGS "${RTEMS_BSP_CFLAGS} -DBSP_${RTEMS_BSP}=1 -ffunction-sections -fdata-sections -O2 -g -isystem${RTEMS_BSP_INCDIR}")
set(RTEMS_LDFLAGS "${RTEMS_BSP_LDFLAGS} -B${RTEMS_BSP_DIR}/lib")
set(RTEMS_EXE_LDFLAGS "${RTEMS_LDFLAGS} ${RTEMS_EXE_BSP_LDFLAGS} -Wl,--gc-sections -B${RTEMS_BSP_DIR}/lib -qrtems")
set(RTEMS_MODULE_LDFLAGS "${RTEMS_LDFLAGS} -Wl,--undefined -r")

if ("${RTEMS_MAJOR}" STREQUAL "4")
    set(RTEMS_LDFLAGS "${RTEMS_LDFLAGS} -specs bsp_specs -qrtems")
endif()

set(CMAKE_C_FLAGS "${RTEMS_CFLAGS}")
set(CMAKE_CXX_FLAGS "${RTEMS_CFLAGS}")
set(CMAKE_EXE_LINKER_FLAGS "${RTEMS_LDFLAGS}")
set(CMAKE_SHARED_LINKER_FLAGS "-Wl,--undefined -Wl,-r -nostdlib")
set(CMAKE_MODULE_LINKER_FLAGS "-Wl,--undefined -Wl,-r -nostdlib")
