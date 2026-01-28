$ws = New-Object -ComObject WScript.Shell
$startup = [Environment]::GetFolderPath('Startup')
$clockPath = Join-Path $env:USERPROFILE "clock\digital_clock.pyw"
$clockDir = Join-Path $env:USERPROFILE "clock"
$sc = $ws.CreateShortcut("$startup\DigitalClock.lnk")
$sc.TargetPath = $clockPath
$sc.WorkingDirectory = $clockDir
$sc.Save()
Write-Host "Done!"
