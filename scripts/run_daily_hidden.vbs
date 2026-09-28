' Runs the daily snapshot without a console window. Log: logs\daily.log
' Python is called by absolute path (per-user install), not whatever "python" is on PATH.
Set sh = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
root = fs.GetParentFolderName(fs.GetParentFolderName(WScript.ScriptFullName))
py = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%\Programs\Python\Python312\python.exe")
If Not fs.FileExists(py) Then
  WScript.Quit 2
End If
sh.CurrentDirectory = root
sh.Run "cmd /c """"" & py & """ scripts\daily_snapshot.py --push >> logs\daily.log 2>&1""", 0, True
