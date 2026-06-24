@echo off
set WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--no-proxy-server
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0manager.pyw"
