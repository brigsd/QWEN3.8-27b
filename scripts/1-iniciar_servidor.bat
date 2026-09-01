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

if errorlevel 6 goto glm_4bit
if errorlevel 5 goto glm_8bit
if errorlevel 4 goto glm_16bit
if errorlevel 3 goto qwen_turbo
if errorlevel 2 goto qwen_128k
if errorlevel 1 goto qwen_64k

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
echo.
echo Iniciando GLM (16-bit FP16 KV Cache)...
call :executar_glm f16 f16 32768
goto fim

:glm_8bit
echo.
echo Iniciando GLM (8-bit Q8_0 KV Cache)...
call :executar_glm q8_0 q8_0 65536
goto fim

:glm_4bit
echo.
echo Iniciando GLM (4-bit Q4_0 KV Cache)...
call :executar_glm q4_0 q4_0 131072
goto fim

:executar_glm
set CTK=%1
set CTV=%2
set CTX=%3

set GLM_MODEL=
for %%F in (..\models\*glm*.gguf ..\models\*GLM*.gguf) do (
    set GLM_MODEL=%%F
)

if "!GLM_MODEL!"=="" (
    echo.
    echo [AVISO] Nenhum arquivo .gguf do GLM foi encontrado em ..\models\
    echo.
    echo Deseja baixar o modelo GLM-4-9B-Chat Q4_K_M (~5.5 GB) agora? (S/N)
    choice /C SN /N /M "Digite S ou N: "
    if errorlevel 2 goto fim
    if errorlevel 1 (
        echo.
        echo Baixando GLM-4-9B-Chat via Hugging Face...
        python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='THUDM/glm-4-9b-chat-GGUF', filename='glm-4-9b-chat.Q4_K_M.gguf', local_dir=r'..\models')"
        set GLM_MODEL=..\models\glm-4-9b-chat.Q4_K_M.gguf
    )
)

echo.
echo Iniciando Servidor com !GLM_MODEL! (Contexto: %CTX% tokens, KV: %CTK%)...
llama-server.exe -m "!GLM_MODEL!" -ngl 99 -fa on -c %CTX% -ctk %CTK% -ctv %CTV% --port 8080 --host 0.0.0.0 -np 1
exit /b

:fim
pause
