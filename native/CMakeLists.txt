cmake_minimum_required(VERSION 3.20)

project(Web3DNative LANGUAGES CXX)

add_library(web3d_native STATIC
  src/web3d_native.cpp
)

target_include_directories(web3d_native
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
)

target_compile_features(web3d_native PUBLIC cxx_std_20)

set_target_properties(web3d_native PROPERTIES
  CXX_EXTENSIONS OFF
  OUTPUT_NAME web3d_native
)

option(WEB3D_BUILD_EXAMPLES "Build Web3D native example executables" ON)

if(WEB3D_BUILD_EXAMPLES)
  add_executable(web3d_native_sandbox
    examples/sandbox.cpp
  )

  target_link_libraries(web3d_native_sandbox
    PRIVATE
      web3d_native
  )
endif()
