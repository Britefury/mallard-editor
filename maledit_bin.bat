@echo off

REM Batch file for launching the Mallard Editor using a binary ZIP distribution of Larch

REM *** Set the path to your Larch binary here
set LARCHPATH=\code\larch2

REM Ensure its set
if not exist %LARCHPATH% goto LARCH_NOT_SET

REM Capture current path; we need it
set MALLARD_EDITOR_PATH=%CD%

REM Set up JYTHONPATH so it can access the necessary stuff
set JYTHONPATH=%LARCHPATH%\bin;%LARCHPATH%\larch;%LARCHPATH%\extlibs\jsoup-1.7.3.jar;%LARCHPATH%\extlibs\svgSalamander.jar;%MALLARD_EDITOR_PATH%

REM Invoke larch starting the Mallard Editor app (app)
cd %LARCHPATH%
call lch -app app
cd %MALLARD_EDITOR_PATH%


:LARCH_NOT_SET
echo Could not find Larch binary at '%LARCHPATH%'. Please edit this batch file and change the line starting with 'set LARCHPATH=' to point to the correct path