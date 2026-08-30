@echo off
title Servidor Local llama.cpp (Qwen3.8-27B - MODO GIGANTE 128K)
cd /d "%~dp0"

echo ========================================================
echo       Verificando hardware e placas de video...
echo ========================================================

set GPU_COUNT=0
for /f %%A in ('llama-server.exe --list-devices 2^>nul ^| findstr /R /C:"CUDA[0-9]:" ^| find /c /v ""') do set GPU_COUNT=%%A

if "%GPU_COUNT%"=="0" (
    for /f %%A in ('nvidia-smi -L 2^>nul ^| findstr /R /C:"^GPU [0-9]:" ^| find /c /v ""') do set GPU_COUNT=%%A
)

echo.
echo Placas detectadas:
llama-server.exe --list-devices 2>nul | findstr /R /C:"CUDA[0-9]:"
echo.

if %GPU_COUNT% GEQ 2 (
    set NGL=99
) else if %GPU_COUNT% EQU 1 (
    set NGL=22
) else (
    set NGL=0
)

echo ========================================================
echo  MODO GIGANTE ATIVADO (128.000 TOKENS / 4-BIT KV CACHE)
echo  - Ideal para Web Chat, leitura de livros e PDFs imensos
echo  - Flash Attention Ativo (-fa on)
echo  - Porta: http://127.0.0.1:8080
echo ========================================================
echo.

llama-server.exe -m "..\models\Qwen3.8-27B-Q4_K_M.gguf" -ngl %NGL% -c 131072 -ctk q4_0 -ctv q4_0 -fa on -np 1 --port 8080 --host 127.0.0.1
pause