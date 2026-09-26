' Runs the daily snapshot without a console window. Log: logs\daily.log
Set sh = CreateObject("WScript.Shell")
root = CreateObject("Scripting.FileSystemObject").GetParentFolderName(CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName))
sh.CurrentDirectory = root
sh.Run "cmd /c python scripts\daily_snapshot.py --push >> logs\daily.log 2>&1", 0, True
