cmake_minimum_required(VERSION 3.20)
project(rtems_test_suite C CXX)

include("../cmake/rtems.cmake")

set(CMAKE_C_STANDARD 99)
set(CMAKE_VERBOSE_MAKEFILE ON)

add_executable(
	rtems_test_suite

	rtems_test_main.c
)

target_link_libraries(
	rtems_test_suite PRIVATE

	rtemsbsp
	rtemscpu
	m
)

if ("${RTEMS_NETWORK_STACK}" STREQUAL "BSD")
	target_link_libraries(
		rtems_test_suite PRIVATE

		bsd
		debugger
		m
	)
endif()


