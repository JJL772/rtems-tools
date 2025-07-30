
# Common configuration
set(RTEMS_ARCH "m68k")
set(RTEMS_VERSION 4.10.2)
set(RTEMS_BSP "uC5282")
set(RTEMS_SUBDIR "rtems_p5")
set(RTEMS_NETWORK_STACK "LEGACY")
set(RTEMS_BSP_CFLAGS "-mcpu=5282 -O2 -g -Wimplicit-function-declaration -Wstrict-prototypes -Wnested-externs")
include ("${CMAKE_CURRENT_LIST_DIR}/rtems-toolchain.cmake")
