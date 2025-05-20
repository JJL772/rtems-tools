# Misc. RTEMS Tools

This is meant to be used in conjunction with [rtems-top](https://github.com/JJL772/rtems-top.git), where it is submoduled in.
Things in here might still be useful to people outside of SLAC, though (particularly the CMake toolchains).

## CMake Usage

cmake/rtems.cmake contains a number of helpers for working with RTEMS in CMake. They are documented throughout that file.

To build a basic application for RTEMS 7 pc686 using CMake, you might write a CMakeLists.txt with the following contents:
```
# Assuming this is submoduled in under tools/
include(tools/cmake/rtems.cmake)
rtems_cmake_init()

add_executable(
    myApp src/rtems_init.c
)
```

And then you'd configure and build with:
```
cmake . -Bbuild -DCMAKE_TOOLCHAIN_FILE=tools/toolchains/rtems7-pc686.cmake
make -C build
```

### Toolchains

CMake toolchain files can be found in the toolchains subdirectory.

These can be used like this:
```
cmake . -Bbuild-i386-rtems -GNinja -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_TOOLCHAIN_FILE=path/to/this/repo/toolchains/rtems6-pc686.cmake
```

The flags provided in the toolchain files comes from the generated Makefile.cfg produced by RTEMS.

