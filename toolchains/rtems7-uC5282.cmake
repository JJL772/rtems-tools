
# Common configuration
set(RTEMS_ARCH "m68k")
set(RTEMS_VERSION 7.0)
set(RTEMS_BSP "uC5282")
set(RTEMS_NETWORK_STACK "BSD")
set(RTEMS_BSP_CFLAGS "-mcpu=5282")
include ("${CMAKE_CURRENT_LIST_DIR}/rtems-toolchain.cmake")
