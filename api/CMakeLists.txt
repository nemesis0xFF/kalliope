cmake_minimum_required(VERSION 3.19)
project(kalliope_api LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_compile_options(-O3 -Wall -Wextra -pedantic)

if (DEFINED CROW_INCLUDE_DIR)
    include_directories(${CROW_INCLUDE_DIR})
endif()

add_definitions(-DCROW_USE_ASIO)

add_executable(kalliope_api main.cpp)
target_link_libraries(kalliope_api PRIVATE sqlite3 pthread)