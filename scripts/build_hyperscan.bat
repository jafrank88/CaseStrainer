@echo off
setlocal

:: Set up Visual Studio environment
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"

:: Set Boost path
set BOOST_ROOT=C:\Users\jafrank\Downloads\boost_1_88_0\boost_1_88_0

:: Create and enter build directory
if not exist hyperscan\hyperscan\build mkdir hyperscan\hyperscan\build
cd hyperscan\hyperscan\build

:: Configure with CMake
cmake .. -DBOOST_ROOT="%BOOST_ROOT%" -DBUILD_EXAMPLES=OFF -DCMAKE_BUILD_TYPE=Release

:: Build
cmake --build . --config Release

:: Return to original directory
cd ..\..\..

echo Build completed! 