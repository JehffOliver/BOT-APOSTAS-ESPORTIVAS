@echo off
call "%~dp0stop.cmd"
timeout /t 1 >nul
call "%~dp0start.cmd"
