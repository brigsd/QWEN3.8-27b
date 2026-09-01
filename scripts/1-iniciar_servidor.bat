@echo off
setlocal enabledelayedexpansion
title Servidor Local de IA (Qwen 3.8 27B / GLM)
cd /d "%~dp0"

cls
echo ====================================================================
echo   SERVIDOR LOCAL DE IA - DUAL GPU (RTX 5070 + RTX 2080 Ti)
echo ====================================================================
echo.
echo Escolha o modelo e a configuracao da Janela de Contexto:
echo.
echo --- [ OPCOES QWEN 3.8 27B ] ----------------------------------------
echo [1] Qwen 27B - Modo Precisao 64k (8-bit KV Cache) - RECOMENDADO
echo     Uso de VRAM: ~20.6 GB - Precisao Maxima para Programacao
echo.
echo [2] Qwen 27B - Modo Gigante 128k (4-bit KV Cache)
echo     Uso de VRAM: ~22.6 GB - Contexto Longo para Documentos e Livros
echo.
echo [3] Qwen 27B - Modo TURBO Especulativo (Draft Model 0.5B)
echo     Acelera a geracao para ~60 a 75 tokens/s
echo.
echo --- [ OPCOES GLM ] -------------------------------------------------
echo [4] GLM - Modo 16-bit FP16 (Precisao Maxima Original)
echo     Janela de Contexto em precisao total sem quantizacao
echo.
echo [5] GLM - Modo 8-bit Q8_0 (Otimizado: Metade da VRAM) - RECOMENDADO
echo     Economiza 50 porcento da VRAM do contexto com ZERO perda
echo.
echo [6] GLM - Modo 4-bit Q4_0 (Contexto Ultra Longo)
echo     Maximo espaco de contexto com menor consumo de memoria
echo.
echo ====================================================================
choice /C 123456 /N /M "Selecione uma opcao (1 a 6): "

set OPCAO=%ERRORLEVEL%

if "%OPCAO%"=="1" goto qwen_64k
if "%OPCAO%"=="2" goto qwen_128k
if "%OPCAO%"=="3" goto qwen_turbo
if "%OPCAO%"=="4" goto glm_16bit
if "%OPCAO%"=="5" goto glm_8bit
if "%OPCAO%"=="6" goto glm_4bit
goto fim

:qwen_64k
echo.
echo Iniciando Qwen 3.8 27B (64k, 8-bit KV)...
llama-server.exe -m ..\models\Qwen3.8-27B-Q4_K_M.gguf --mmproj ..\models\mmproj-Qwen3.8-27B-f16.gguf -ngl 99 -fa on -c 65536 -ctk q8_0 -ctv q8_0 --port 8080 --host 0.0.0.0 -np 1
goto fim

:qwen_128k
echo.
echo Iniciando Qwen 3.8 27B (128k, 4-bit KV)...
llama-server.exe -m ..\models\Qwen3.8-27B-Q4_K_M.gguf --mmproj ..\models\mmproj-Qwen3.8-27B-f16.gguf -ngl 99 -fa on -c 131072 -ctk q4_0 -ctv q4_0 --port 8080 --host 0.0.0.0 -np 1
goto fim

:qwen_turbo
echo.
echo Iniciando Qwen 3.8 27B TURBO com Speculative Decoding...
llama-server.exe -m ..\models\Qwen3.8-27B-Q4_K_M.gguf -md ..\models\qwen2.5-0.5b-instruct-q4_k_m.gguf -ngld 99 --spec-draft-n-max 4 --mmproj ..\models\mmproj-Qwen3.8-27B-f16.gguf -ngl 99 -fa on -c 65536 -ctk q8_0 -ctv q8_0 --port 8080 --host 0.0.0.0 -np 1
goto fim

:glm_16bit
set CTK=f16
set CTV=f16
set CTX=32768
goto rodar_glm

:glm_8bit
set CTK=q8_0
set CTV=q8_0
set CTX=65536
goto rodar_glm

:glm_4bit
set CTK=q4_0
set CTV=q4_0
set CTX=131072
goto rodar_glm

:rodar_glm
set GLM_FILE=
for %%F in (..\models\*glm*.gguf ..\models\*GLM*.gguf) do (
    set GLM_FILE=%%F
)

if "!GLM_FILE!"=="" (
    echo.
    echo ====================================================================
    echo [AVISO] Modelo GLM (.gguf) nao encontrado na pasta models.
    echo Baixando GLM-4-9B-Chat Q4_K_M automaticamente...
    echo ====================================================================
    python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='bartowski/glm-4-9b-chat-GGUF', filename='glm-4-9b-chat-Q4_K_M.gguf', local_dir=r'..\models')"
    set GLM_FILE=..\models\glm-4-9b-chat-Q4_K_M.gguf
)

echo.
echo Iniciando Servidor GLM: !GLM_FILE!
echo Parametros: Contexto %CTX% tokens - KV Cache: %CTK%
echo.
llama-server.exe -m "!GLM_FILE!" -ngl 99 -fa on -c %CTX% -ctk %CTK% -ctv %CTV% --port 8080 --host 0.0.0.0 -np 1
goto fim

:fim
pause
