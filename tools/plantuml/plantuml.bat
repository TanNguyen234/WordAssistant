@echo off
setlocal
set "DIR=%~dp0"
java -Djava.awt.headless=true -jar "%DIR%plantuml.jar" -charset UTF-8 %*
