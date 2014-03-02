@echo off

REM *** Set the path to your Larch JAR here
set LARCH_JAR_PATH=larch-in-a-jar-0.1.33-alpha.jar

REM Check its correct
if not exist %LARCH_JAR_PATH% goto LARCH_JAR_NOT_SET

REM Invoke larch starting the Mallard Editor app (app)
java -jar %LARCH_JAR_PATH% -app app

goto :eof

:LARCH_JAR_NOT_SET
echo Could not find Larch JAR at '%LARCH_JAR_PATH%'. Please edit this batch file and change the line starting with 'set LARCH_JAR_PATH=' to point to the correct path
