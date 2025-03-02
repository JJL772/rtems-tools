# Additional tools for RTEMS

include(GNUInstallDirs)

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
