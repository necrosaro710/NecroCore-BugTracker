Option Explicit
Dim shell, fs, root, pythonw, script, cmd
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
root = fs.GetParentFolderName(WScript.ScriptFullName)
pythonw = root & "\runtime\pythonw.exe"
script = root & "\necro_screenshot_client.py"
cmd = Chr(34) & pythonw & Chr(34) & " " & Chr(34) & script & Chr(34) & " --run"
shell.Run cmd, 0, False
