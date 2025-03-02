# Additional tools for RTEMS

include(GNUInstallDirs)

# Helper command to add an ELF executable and generate a bootable image from it
function(rtems_add_executable TARGET )
    add_executable(
        ${TARGET} ${ARGN}
    )

    add_custom_command(
        OUTPUT "${CMAKE_BINARY_DIR}/${TARGET}.boot"
        COMMAND "${CMAKE_OBJCOPY}" -O binary "${TARGET}" "${TARGET}.boot"
        DEPENDS "${CMAKE_BINARY_DIR}/${TARGET}"
        COMMENT "Generating bootable image ${TARGET}.boot"
    )
    
    add_custom_target(
        "${TARGET}-boot" ALL
        DEPENDS "${CMAKE_BINARY_DIR}/${TARGET}.boot"
    )
    
    # Install to an EPICS-style "shared" prefix
    if (SHARED_PREFIX)
        install(
            TARGETS "${TARGET}"
            
            RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}/RTEMS-${RTEMS_BSP}"
            LIBRARY DESTINATION "${CMAKE_INSTALL_LIBDIR}/RTEMS-${RTEMS_BSP}"
            ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}/RTEMS-${RTEMS_BSP}"
        )
        install(
            FILES "${CMAKE_BINARY_DIR}/${TARGET}.boot"
            DESTINATION "${CMAKE_INSTALL_BINDIR}/RTEMS-${RTEMS_BSP}"
        )
    else()
        install(TARGETS "${TARGET}-boot" "${TARGET}")
        install(
            FILES "${CMAKE_BINARY_DIR}/${TARGET}.boot"
            DESTINATION "${CMAKE_INSTALL_BINDIR}"
        )
    endif()
endfunction()

# Helper function to add and generate a rootfs.
# This will automatically add the rootfs.c file to your target. call rootfs_unpack() to unpack at runtime
function(rtems_add_rootfs TARGET DIR)
    # Generate list of files we'll depend on
    file(GLOB_RECURSE ROOTFS_FILES "${DIR}/**")

    add_custom_command(
        OUTPUT "${CMAKE_BINARY_DIR}/${TARGET}-rootfs.c"
        COMMAND "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../mkrootfs.py" -o "${CMAKE_BINARY_DIR}/${TARGET}-rootfs.c" -i "${DIR}"
        DEPENDS ${ROOTFS_FILES}
    )
    
    #add_custom_target(
    #    "${TARGET}-rootfs" ALL
    #    DEPENDS "${CMAKE_BINARY_DIR}/rootfs.c"
    #)
    
    # Add rootfs sources to target
    target_sources(
        ${TARGET} PRIVATE "${CMAKE_BINARY_DIR}/${TARGET}-rootfs.c"
    )
endfunction()
