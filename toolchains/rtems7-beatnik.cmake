
# Common configuration
set(RTEMS_ARCH "powerpc")
set(RTEMS_VERSION 7.0)
set(RTEMS_BSP "beatnik")
set(RTEMS_BSP_CFLAGS "-mcpu=7400")
set(RTEMS_NETWORK_STACK "BSD")
include ("${CMAKE_CURRENT_LIST_DIR}/rtems-toolchain.cmake")
