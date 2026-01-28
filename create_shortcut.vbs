Set WshShell = CreateObject("WScript.Shell")
strStartup = WshShell.SpecialFolders("Startup")
Set oShortcut = WshShell.CreateShortcut(strStartup & "\DigitalClock.lnk")
oShortcut.TargetPath = "C:\Users\이동옥\clock\digital_clock.pyw"
oShortcut.WorkingDirectory = "C:\Users\이동옥\clock"
oShortcut.Save
WScript.Echo "시작프로그램에 등록 완료!"
