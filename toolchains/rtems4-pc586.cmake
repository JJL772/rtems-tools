
# Common configuration
set(RTEMS_ARCH "i386")
set(RTEMS_VERSION 4.10.2)
set(RTEMS_BSP "pc586")
set(RTEMS_SUBDIR "rtems_p5")
set(RTEMS_NETWORK_STACK "LEGACY")
set(RTEMS_BSP_CFLAGS "-march=pentium -O2 -g -Wall -Wimplicit-function-declaration -Wstrict-prototypes -Wnested-externs")
set(RTEMS_EXE_BSP_LDFLAGS "-Wl,-Ttext,0x100000")
include ("${CMAKE_CURRENT_LIST_DIR}/rtems-toolchain.cmake")
