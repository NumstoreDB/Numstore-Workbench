# FindNumstore.cmake
# Vendored find module for Numstore.
#
# User-configurable options (set before calling find_package or via -D):
#   NUMSTORE_ENABLE_NDEBUG   - build in release mode (default ON)
#   NUMSTORE_ENABLE_NLOG     - build without logs (default ON)
#   NUMSTORE_ENABLE_PORTABLE - build in portable mode (default ON)
#   NUMSTORE_ENABLE_STRIP    - strip symbols (default ON)
#   NUMSTORE_ENABLE_ASAN     - build with address sanitizer (default OFF)
#
# Provides:
#   Numstore::Numstore     - imported target
#   Numstore_INCLUDE_DIR   - public include directory
#   Numstore_SRC_DIR       - private src directory
#   Numstore_FOUND         - true if found

# User-configurable
set(ENABLE_NDEBUG   ON  CACHE BOOL "Build Numstore in release mode"           FORCE)
set(ENABLE_NLOG     ON  CACHE BOOL "Build Numstore without logs"              FORCE)
set(ENABLE_PORTABLE ON  CACHE BOOL "Build Numstore in portable mode"          FORCE)
set(ENABLE_STRIP    ON  CACHE BOOL "Strip symbols in Numstore library"        FORCE)
set(ENABLE_ASAN     OFF CACHE BOOL "Build Numstore with address sanitizer"    FORCE)

# Internal — not user-facing
set(ENABLE_NTEST  ON )
set(BUILD_TOOLS   OFF)
set(BUILD_SAMPLES OFF)
set(BUILD_APP     OFF)

set(_numstore_source_dir ${CMAKE_SOURCE_DIR}/thirdparty/numstore)

if(NOT EXISTS "${_numstore_source_dir}/CMakeLists.txt")
  message(FATAL_ERROR "FindNumstore: source not found at ${_numstore_source_dir}. "
                      "Did you forget to initialize submodules?")
endif()

if(NOT TARGET numstore)
  add_subdirectory(${_numstore_source_dir} ${CMAKE_BINARY_DIR}/thirdparty/numstore)
endif()

if(NOT TARGET Numstore::Numstore)
  add_library(Numstore::Numstore ALIAS numstore)
endif()

set(Numstore_INCLUDE_DIR ${_numstore_source_dir}/include)
set(Numstore_SRC_DIR     ${_numstore_source_dir}/src)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Numstore
  REQUIRED_VARS Numstore_INCLUDE_DIR
)
