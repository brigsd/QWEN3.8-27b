# Script para baixar os binarios do llama.cpp com suporte a CUDA
$serverDir = Join-Path (Get-Item $PSScriptRoot).Parent.FullName "server"
if (-not (Test-Path $serverDir)) {
    New-Item -ItemType Directory -Path $serverDir -Force | Out-Null
}

$binZip = Join-Path $serverDir "llama-cuda.zip"
$cuZip  = Join-Path $serverDir "cudart.zip"

$binUrl = "https://github.com/ggml-org/llama.cpp/releases/download/b10679/llama-b10679-bin-win-cuda-13.0-x64.zip"
$cuUrl  = "https://github.com/ggml-org/llama.cpp/releases/download/b10679/cudart-llama-bin-win-cuda-13.0-x64.zip"

Write-Host "Baixando binarios do llama.cpp (CUDA 13)..." -ForegroundColor Cyan
& curl.exe --ssl-no-revoke -L -o $binZip $binUrl
Write-Host "Baixando bibliotecas de runtime CUDA..." -ForegroundColor Cyan
& curl.exe --ssl-no-revoke -L -o $cuZip $cuUrl

Write-Host "Extraindo arquivos para $serverDir..." -ForegroundColor Green
Expand-Archive -Path $binZip -DestinationPath $serverDir -Force
Expand-Archive -Path $cuZip -DestinationPath $serverDir -Force

Remove-Item $binZip -Force -ErrorAction SilentlyContinue
Remove-Item $cuZip -Force -ErrorAction SilentlyContinue

Write-Host "Servidor llama.cpp configurado com sucesso!" -ForegroundColor Green
