add_executable(big_file_inner_insert main.c big_file_inner_insert.c)
target_compile_definitions(big_file_inner_insert PRIVATE _GNU_SOURCE)
target_include_directories(big_file_inner_insert 
  PRIVATE "${PROJECT_SOURCE_DIR}/thirdparty/numstore/include"
          "${PROJECT_SOURCE_DIR}/thirdparty/numstore/src"
)
target_link_libraries(big_file_inner_insert numstore)
