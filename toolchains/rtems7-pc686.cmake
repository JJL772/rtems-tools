
# Common configuration
set(RTEMS_ARCH "i386")
set(RTEMS_VERSION 7.0)
set(RTEMS_BSP "pc686")
set(RTEMS_NETWORK_STACK "BSD")
set(RTEMS_BSP_CFLAGS "-O2 -g -fdata-sections -ffunction-sections -mtune=pentiumpro -march=pentium")
include ("${CMAKE_CURRENT_LIST_DIR}/rtems-toolchain.cmake")
