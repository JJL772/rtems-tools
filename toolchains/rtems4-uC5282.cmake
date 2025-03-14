
# Common configuration
set(RTEMS_ARCH "m68k")
set(RTEMS_VERSION 4)
set(RTEMS_BSP "uC5282")
set(RTEMS_BSP_CFLAGS "-mcpu=5282 -O2 -g -Wimplicit-function-declaration -Wstrict-prototypes -Wnested-externs -DRTEMS_LEGACY_STACK=1")
include ("${CMAKE_CURRENT_LIST_DIR}/rtems-toolchain.cmake")
