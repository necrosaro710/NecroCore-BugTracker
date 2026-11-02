Option Explicit
Dim sh, fs, root, target, link
Set sh = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
root = fs.GetParentFolderName(WScript.ScriptFullName)
target = sh.SpecialFolders("Startup") & "\NecroCore_ScreenshotClient.lnk"
If fs.FileExists(target) Then
  WScript.Echo "AutoStart already exists, not overwritten: " & target
Else
  Set link = sh.CreateShortcut(target)
  link.TargetPath = sh.ExpandEnvironmentStrings("%SystemRoot%") & "\System32\wscript.exe"
  link.Arguments = Chr(34) & root & "\launch_hidden.vbs" & Chr(34)
  link.WorkingDirectory = root
  link.Description = "NecroCore screenshot transfer on this WoW PC"
  link.Save
  WScript.Echo "AutoStart enabled for this Windows user."
End If
