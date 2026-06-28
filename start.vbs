Set WshShell = CreateObject("WScript.Shell")

WshShell.Run "cmd /c ""cd /d F:\make_jobs\backend & .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000""", 0, False

WScript.Sleep 2000

WshShell.Run "cmd /c ""cd /d F:\make_jobs\frontend & node_modules\.bin\vite.cmd --host 127.0.0.1""", 0, False

MsgBox "make-jobs-ai started!" & vbCrLf & vbCrLf & "Backend: http://127.0.0.1:8000" & vbCrLf & "Frontend: http://127.0.0.1:5173" & vbCrLf & vbCrLf & "Run stop.bat to stop.", vbInformation, "make-jobs-ai"
