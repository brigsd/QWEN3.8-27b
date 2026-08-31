# Script para baixar o modelo rascunho de 0.5B (Speculative Decoding)
$modelsDir = Join-Path (Get-Item $PSScriptRoot).Parent.FullName "models"
New-Item -ItemType Directory -Path $modelsDir -Force | Out-Null

Write-Host "Instalando huggingface_hub..." -ForegroundColor Cyan
pip install huggingface_hub

$destFile = Join-Path $modelsDir "qwen2.5-0.5b-instruct-q4_k_m.gguf"
Write-Host "Baixando qwen2.5-0.5b-instruct-q4_k_m.gguf (~397 MB) para $modelsDir..." -ForegroundColor Green

python -c @"
from huggingface_hub import hf_hub_download
import sys
hf_hub_download(
    repo_id='Qwen/Qwen2.5-0.5B-Instruct-GGUF',
    filename='qwen2.5-0.5b-instruct-q4_k_m.gguf',
    local_dir=r'$modelsDir'
)
print('Download concluido com sucesso!')
"@
