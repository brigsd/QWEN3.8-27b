# Script para baixar o modelo Qwen 3.8 27B quantizado
Write-Host "Instalando huggingface_hub..." -ForegroundColor Cyan
pip install -U huggingface_hub

$dest = Join-Path (Get-Item $PSScriptRoot).Parent.FullName "models"
New-Item -ItemType Directory -Path $dest -Force | Out-Null

Write-Host "Baixando Qwen3.8-27B-Q4_K_M.gguf para $dest..." -ForegroundColor Green
hf download Qwen/Qwen3.8-27B-GGUF Qwen3.8-27B-Q4_K_M.gguf --local-dir $dest