$serverDir = Join-Path (Get-Item $PSScriptRoot).Parent.FullName "server"
$agentDir = Join-Path (Get-Item $PSScriptRoot).Parent.FullName "agent"
$WshShell = New-Object -ComObject WScript.Shell
$desktop = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)

$s1 = $WshShell.CreateShortcut("$desktop\1 - Iniciar Servidor Qwen 27B.lnk")
$s1.TargetPath = "$serverDir\1-iniciar_servidor_llama.bat"
$s1.WorkingDirectory = $serverDir
$s1.Save()

$s1b = $WshShell.CreateShortcut("$desktop\1b - Iniciar Servidor Direto (128k Gigante).lnk")
$s1b.TargetPath = "$serverDir\1-iniciar_servidor_128k_gigante.bat"
$s1b.WorkingDirectory = $serverDir
$s1b.Save()

$s2 = $WshShell.CreateShortcut("$desktop\2 - Abrir Claude Code Local (Aider).lnk")
$s2.TargetPath = "$serverDir\2-iniciar_aider_com_llama.bat"
$s2.WorkingDirectory = $serverDir
$s2.Save()

$s3 = $WshShell.CreateShortcut("$desktop\3 - Abrir Agente Nativo (Qwen 27B).lnk")
$s3.TargetPath = "$serverDir\3-iniciar_agente_nativo.bat"
$s3.WorkingDirectory = $agentDir
$s3.Save()

Write-Host "Atalhos criados com sucesso na Area de Trabalho!" -ForegroundColor Green