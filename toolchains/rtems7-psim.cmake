
# Common configuration
set(RTEMS_ARCH "powerpc")
set(RTEMS_VERSION 7.0)
set(RTEMS_BSP "psim")
set(RTEMS_NETWORK_STACK "BSD")
set(RTEMS_BSP_CFLAGS "-Dppc603e -meabi -mcpu=603e -msdata=sysv")
include ("${CMAKE_CURRENT_LIST_DIR}/rtems-toolchain.cmake")
