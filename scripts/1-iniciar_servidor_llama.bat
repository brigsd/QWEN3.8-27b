@echo off
title Servidor Local llama.cpp (Qwen3.8-27B)
cd /d "%~dp0"

echo ========================================================
echo       Verificando hardware e placas de video...
echo ========================================================

:: 1. Detectar dispositivos CUDA disponiveis diretamente pelo llama-server
set GPU_COUNT=0
for /f %%A in ('llama-server.exe --list-devices 2^>nul ^| findstr /R /C:"CUDA[0-9]:" ^| find /c /v ""') do set GPU_COUNT=%%A

:: 2. Fallback com nvidia-smi para garantir que nenhuma placa seja ignorada
if "%GPU_COUNT%"=="0" (
    for /f %%A in ('nvidia-smi -L 2^>nul ^| findstr /R /C:"^GPU [0-9]:" ^| find /c /v ""') do set GPU_COUNT=%%A
)

echo.
echo Placas detectadas:
llama-server.exe --list-devices 2>nul | findstr /R /C:"CUDA[0-9]:"
echo.

if %GPU_COUNT% GEQ 2 goto :DUAL_GPU
if %GPU_COUNT% EQU 1 goto :SINGLE_GPU
goto :NO_GPU

:DUAL_GPU
echo ========================================================
echo  [CONFIGURACAO] MODO DUAL GPU ATIVADO! (%GPU_COUNT% placas encontradas)
echo  - Carregando 100%% das camadas diretamente na VRAM.
echo  - RTX 5070 (12GB) + RTX 2080 Ti (11GB) = 23GB de VRAM.
echo  - Maxima velocidade de resposta.
echo ========================================================
set NGL=99
goto :START_SERVER

:SINGLE_GPU
echo ========================================================
echo  [CONFIGURACAO] MODO GPU UNICA ATIVADO! (1 placa encontrada)
echo  - Configurando 22 camadas na GPU e restante na RAM DDR5.
echo  - Protecao contra estouro de VRAM na placa principal.
echo ========================================================
set NGL=22
goto :START_SERVER

:NO_GPU
echo ========================================================
echo  [AVISO] Nenhuma GPU CUDA detectada.
echo  - Rodando em modo CPU na memoria RAM.
echo ========================================================
set NGL=0
goto :START_SERVER

:START_SERVER
echo.
echo ========================================================
echo   ESCOLHA O MODO DE CONTEXTO:
echo   [1] 64k Tokens (8-bit)  - Codigo e Alta Precisao (Padrao)
echo   [2] 128k Tokens (4-bit) - Modo Gigante para Leitura e PDFs
echo ========================================================
set MODO=1
set /p MODO="Digite 1 ou 2 (Pressione ENTER para 64k): "

if "%MODO%"=="2" (
    echo.
    echo  -> Ativando MODO GIGANTE: 128.000 tokens com KV Cache em 4-bit (q4_0)
    set CTX=131072
    set CTK=q4_0
    set CTV=q4_0
) else (
    echo.
    echo  -> Ativando MODO PRECISAO: 64.000 tokens com KV Cache em 8-bit (q8_0)
    set CTX=65536
    set CTK=q8_0
    set CTV=q8_0
)

echo.
echo Iniciando servidor em: http://127.0.0.1:8080 (Contexto: %CTX% tokens)
echo ========================================================
echo.

llama-server.exe -m "..\models\Qwen3.8-27B-Q4_K_M.gguf" -ngl %NGL% -c %CTX% -ctk %CTK% -ctv %CTV% -fa on -np 1 --port 8080 --host 127.0.0.1
pause
