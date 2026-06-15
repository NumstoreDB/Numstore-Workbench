add_executable(inner_insert src/main.c src/inner_insert.c)
target_compile_definitions(inner_insert PRIVATE _GNU_SOURCE)
target_include_directories(inner_insert 
  PRIVATE "${PROJECT_SOURCE_DIR}/thirdparty/numstore/include"
          "${PROJECT_SOURCE_DIR}/thirdparty/numstore/src"
)
target_link_libraries(inner_insert numstore)
