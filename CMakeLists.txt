################### Meta Information
cmake_minimum_required(VERSION 3.18)

## Read the version from version.txt
file(STRINGS "${CMAKE_SOURCE_DIR}/version.txt" NUMSTORE_VERSION LIMIT_COUNT 1)

project(numstore-workbench
    VERSION     "${NUMSTORE_VERSION}"
    DESCRIPTION "Performance tests for numstore"
    LANGUAGES   C
)

set(CMAKE_C_STANDARD 11)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

############################## Set up dependencies
list(APPEND CMAKE_MODULE_PATH ${CMAKE_SOURCE_DIR}/cmake)
find_package(Numstore REQUIRED)

add_subdirectory(performance/big_file_inner_insert)
