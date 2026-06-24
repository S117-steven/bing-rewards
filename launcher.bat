@echo off
set WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS=--no-proxy-server
start "" pythonw "%~dp0manager.pyw"
