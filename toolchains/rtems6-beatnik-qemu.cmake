
# Common configuration
set(RTEMS_ARCH "powerpc")
set(RTEMS_VERSION 6.0)
set(RTEMS_BSP "beatnik")
set(RTEMS_BSP_CFLAGS "-mcpu=7400")
set(CMAKE_CXX_FLAGS "-DRTEMS_LIBBSD_STACK=1")
set(CMAKE_C_FLAGS "-DRTEMS_LIBBSD_STACK=1")
set(RTEMS_BSP_LDFLAGS "-Wl,-Ttext,0x100000")
set(RTEMS_NETWORK_STACK "BSD")
include ("${CMAKE_CURRENT_LIST_DIR}/rtems.cmake")
