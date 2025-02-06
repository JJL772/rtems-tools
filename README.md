# Misc. RTEMS Tools

This is meant to be used in conjunction with [rtems-top](https://github.com/JJL772/rtems-top.git), where it is submoduled in.
Things in here might still be useful to people outside of SLAC, though (particularly the CMake toolchains).

## CMake Toolchains

CMake toolchain files can be found in the toolchains subdirectory.

These can be used like this:
```
cmake . -Bbuild-i386-rtems -GNinja -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_TOOLCHAIN_FILE=path/to/this/repo/toolchains/rtems6-pc686.cmake
```

The flags provided in the toolchain files comes from the generated Makefile.cfg produced by RTEMS.

