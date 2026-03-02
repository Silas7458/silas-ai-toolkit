' launch-hidden.vbs — Launches a PowerShell script with zero console flash.
' Usage: wscript.exe launch-hidden.vbs "C:\path\to\script.ps1"
' The key: WScript is a GUI host, so no conhost.exe is ever created.

If WScript.Arguments.Count = 0 Then
    WScript.Quit 1
End If

Dim psPath, scriptPath
psPath = "powershell.exe"
scriptPath = WScript.Arguments(0)

Dim shell
Set shell = CreateObject("WScript.Shell")
shell.Run psPath & " -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & scriptPath & """", 0, True
