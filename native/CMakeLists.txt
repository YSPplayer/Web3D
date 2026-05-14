#cmake -S D:\YueShaoPu\Web3D\native -B D:\YueShaoPu\Web3D\native\build
#cmake --build D:\YueShaoPu\Web3D\native\build --config Debug

cmake_minimum_required(VERSION 3.20)

project(deep_lr LANGUAGES CXX)

set(PACKAGE_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/Package" CACHE PATH "Third-party package root")

if(NOT EXISTS "${PACKAGE_ROOT}")
    message(FATAL_ERROR "PACKAGE_ROOT does not exist: ${PACKAGE_ROOT}")
endif()

set(PACKAGE_INCLUDE_DIR "${PACKAGE_ROOT}/include")
set(PACKAGE_LIB_DEBUG_DIR "${PACKAGE_ROOT}/lib/Debug")
set(PACKAGE_LIB_RELEASE_DIR "${PACKAGE_ROOT}/lib/Release")

add_executable(deep_lr
    src/main.cpp
    src/Web/websocket.h
    src/log.h
    src/Web/websocket.cpp
    src/Web/webprocess.h
    src/Web/webprocess.cpp
    src/Neural/sample.h
    src/Neural/sample.cpp
    src/Neural/tensor.h
    src/Neural/tensor.cpp
    src/Neural/layer.h
    src/Neural/layer.cpp
    src/Neural/conv2d.h
    src/Neural/conv2d.cpp
    src/Neural/relu.h
    src/Neural/relu.cpp
    src/Neural/maxpool.h
    src/Neural/maxpool.cpp
    src/Neural/flatten.h
    src/Neural/flatten.cpp
    src/Neural/linear.h
    src/Neural/linear.cpp
    src/Neural/softmax.h
    src/Neural/softmax.cpp
    src/Neural/loss.h
    src/Neural/loss.cpp
    src/define.h
    src/data.h
)

target_compile_features(deep_lr PRIVATE cxx_std_20)

set_target_properties(deep_lr PROPERTIES
    CXX_EXTENSIONS OFF
    OUTPUT_NAME deep_lr
)

target_include_directories(deep_lr PRIVATE
    "${PACKAGE_INCLUDE_DIR}"
)

if(MSVC)
    target_compile_definitions(deep_lr PRIVATE
        _CRT_SECURE_NO_WARNINGS
        NOMINMAX
        WIN32_LEAN_AND_MEAN
        POCO_NO_AUTOMATIC_LIBS
        POCO_STATIC
    )
endif()

target_link_libraries(deep_lr PRIVATE
    debug "${PACKAGE_LIB_DEBUG_DIR}/opencv_core490d.lib"
    optimized "${PACKAGE_LIB_RELEASE_DIR}/opencv_core490.lib"

    debug "${PACKAGE_LIB_DEBUG_DIR}/opencv_imgcodecs490d.lib"
    optimized "${PACKAGE_LIB_RELEASE_DIR}/opencv_imgcodecs490.lib"

    debug "${PACKAGE_LIB_DEBUG_DIR}/opencv_imgproc490d.lib"
    optimized "${PACKAGE_LIB_RELEASE_DIR}/opencv_imgproc490.lib"

    debug "${PACKAGE_LIB_DEBUG_DIR}/PocoFoundationd.lib"
    optimized "${PACKAGE_LIB_RELEASE_DIR}/PocoFoundation.lib"

    debug "${PACKAGE_LIB_DEBUG_DIR}/PocoNetd.lib"
    optimized "${PACKAGE_LIB_RELEASE_DIR}/PocoNet.lib"

    ws2_32
    mswsock
    iphlpapi
)
