# Additional tools for RTEMS

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
endfunction()
