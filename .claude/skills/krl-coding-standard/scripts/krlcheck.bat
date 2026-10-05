@echo off
title krlcheck

rem ============================================================
rem  krlcheck.bat -- drag and drop launcher
rem
rem  Put this next to krlcheck.py.
rem
rem  Usage
rem    - drop .src / .dat files onto this file
rem    - drop a folder onto this file
rem    - double click with nothing: checks the folder this file is in
rem
rem  This file is ASCII only on purpose. cmd.exe can mis-split
rem  UTF-8 multibyte characters in batch files and then try to run
rem  the fragments as commands. Japanese text comes from krlcheck.py.
rem
rem  Arguments are passed to Python exactly as Explorer supplies
rem  them. Explorer already quotes paths that contain spaces, so
rem  this file must NOT rebuild or re-quote them.
rem ============================================================

set "KRLCHECK_OPTS="

set "HERE=%~dp0"
set "SCRIPT=%HERE%krlcheck.py"

if not exist "%SCRIPT%" (
    echo.
    echo   krlcheck.py not found.
    echo   Put this .bat in the same folder as krlcheck.py.
    echo   Looked in: %SCRIPT%
    echo.
    pause
    exit /b 2
)

set "PY="
where py >nul 2>&1 && set "PY=py"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY where python3 >nul 2>&1 && set "PY=python3"

if not defined PY (
    echo.
    echo   Python not found.
    echo   Install it from python.org and tick "Add Python to PATH".
    echo.
    pause
    exit /b 2
)

echo ============================================================
if "%~1"=="" (
    echo No target given. Checking this folder:
    echo   %HERE%
    echo.
    rem trailing "." keeps the closing quote from being escaped by "\"
    %PY% "%SCRIPT%" %KRLCHECK_OPTS% "%HERE%."
) else (
    %PY% "%SCRIPT%" %KRLCHECK_OPTS% %*
)
set "RC=%ERRORLEVEL%"
echo ============================================================

if "%RC%"=="0" echo RESULT: no ERROR
if "%RC%"=="1" echo RESULT: ERROR found. Fix before loading onto the robot.
if "%RC%"=="2" echo RESULT: no target files, or the path is wrong.
if "%RC%"=="3" echo RESULT: krlcheck itself crashed. This is NOT a check result.

echo.
pause
exit /b %RC%
