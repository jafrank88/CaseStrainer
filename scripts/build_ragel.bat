@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cd /d "%~dp0"
cd ragel-6.10
configure
nmake
echo Build complete. Copying ragel.exe to tools directory...
mkdir "%USERPROFILE%\tools" 2>nul
copy ragel\ragel.exe "%USERPROFILE%\tools\"
echo Done! Ragel has been installed to %USERPROFILE%\tools\ragel.exe 