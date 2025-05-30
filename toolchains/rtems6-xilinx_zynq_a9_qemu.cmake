
# Common configuration
set(RTEMS_ARCH "arm")
set(RTEMS_VERSION 6.0)
set(RTEMS_BSP "xilinx_zynq_a9_qemu")
set(RTEMS_NETWORK_STACK "BSD")
set(RTEMS_BSP_CFLAGS "-march=armv7-a -mthumb -mfpu=neon -mfloat-abi=hard -mtune=cortex-a9")
include ("${CMAKE_CURRENT_LIST_DIR}/rtems-toolchain.cmake")
