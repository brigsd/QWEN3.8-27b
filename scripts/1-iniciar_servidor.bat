@echo off
setlocal enabledelayedexpansion
title Servidor Local de IA (Qwen 3.8 27B / GLM-5.3-Flash 321B)
cd /d "%~dp0"

cls
echo ====================================================================
echo   SERVIDOR LOCAL DE IA - DUAL GPU (RTX 5070 + RTX 2080 Ti)
echo ====================================================================
echo.
echo Escolha o modelo e a configuracao de execucao:
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
echo --- [ OPCOES GLM-5.3-FLASH (321B MoE) - C:\glm53_i4 ] -------------
echo [4] GLM-5.3 (321B) - Modo Precisao Total (Policy Quality)
echo     Execucao completa com maxima fidelidade nos 62 shards
echo.
echo [5] GLM-5.3 (321B) - Modo Otimizado (Auto-Tier Balanceado) - RECOMENDADO
echo     Gerenciamento automatico de VRAM e cache de experts
echo.
echo [6] GLM-5.3 (321B) - Modo Turbo Fast (Experimental Fast)
echo     Latencia reduzida para respostas ultra ageis
echo.
echo ====================================================================
choice /C 123456 /N /M "Selecione uma opcao (1 a 6): "

set OPCAO=%ERRORLEVEL%

if "%OPCAO%"=="1" goto qwen_64k
if "%OPCAO%"=="2" goto qwen_128k
if "%OPCAO%"=="3" goto qwen_turbo
if "%OPCAO%"=="4" goto glm_quality
if "%OPCAO%"=="5" goto glm_balanced
if "%OPCAO%"=="6" goto glm_fast
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

:glm_quality
echo.
echo Iniciando Servidor GLM-5.3-Flash 321B (Modo Quality)...
python ..\colibri\c\coli serve --model "C:\glm53_i4" --policy quality --port 8080
goto fim

:glm_balanced
echo.
echo Iniciando Servidor GLM-5.3-Flash 321B (Modo Auto-Tier Balanceado)...
python ..\colibri\c\coli serve --model "C:\glm53_i4" --auto-tier --policy balanced --port 8080
goto fim

:glm_fast
echo.
echo Iniciando Servidor GLM-5.3-Flash 321B (Modo Experimental Fast)...
python ..\colibri\c\coli serve --model "C:\glm53_i4" --policy experimental-fast --port 8080
goto fim

:fim
pause
