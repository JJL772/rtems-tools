
# Common configuration
set(RTEMS_ARCH "i386")
set(RTEMS_VERSION 6)
set(RTEMS_BSP "pc686")
set(RTEMS_BSP_CFLAGS "-O2 -g -fdata-sections -ffunction-sections -mtune=pentiumpro -march=pentium -DQEMU_FIXUPS=1 -DRTEMS_LIBBSD_STACK=1")
set(RTEMS_BSP_LDFLAGS "-Wl,-Ttext,0x100000")
include ("${CMAKE_CURRENT_LIST_DIR}/rtems-toolchain.cmake")
