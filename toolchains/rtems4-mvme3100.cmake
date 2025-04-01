
# Common configuration
set(RTEMS_ARCH "powerpc")
set(RTEMS_VERSION 4.10.2)
set(RTEMS_BSP "mvme3100")
set(RTEMS_SUBDIR "rtems_p4")
set(RTEMS_NETWORK_STACK "LEGACY")
set(RTEMS_BSP_CFLAGS "-mcpu=powerpc -msoft-float -D__ppc_generic -O2 -g -Wimplicit-function-declaration -Wstrict-prototypes -Wnested-externs")
include ("${CMAKE_CURRENT_LIST_DIR}/rtems-toolchain.cmake")
