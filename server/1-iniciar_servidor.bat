@echo off
setlocal enabledelayedexpansion
title Servidor Qwen 3.8 27B Dual GPU (RTX 5070 + RTX 2080 Ti)
cd /d "%~dp0"

cls
echo ====================================================================
echo   SERVIDOR QWEN 3.8 27B - DUAL GPU (RTX 5070 12GB + RTX 2080 Ti 11GB)
echo ====================================================================
echo.
echo Escolha a configuracao de execucao:
echo.
echo [1] Qwen 27B - Modo Precisao 64k (8-bit KV Cache + Visao Multimodal) - RECOMENDADO
echo     Uso de VRAM: ~21.0 GB - Velocidade Maxima (~40 tok/s) para Programacao e Imagens
echo.
echo [2] Qwen 27B - Modo Gigante 128k (4-bit KV Cache Puro)
echo     Uso de VRAM: ~21.5 GB - Contexto Ultra Longo para Grandes Projetos e Documentos
echo.
echo ====================================================================
choice /C 12 /N /M "Selecione uma opcao (1 ou 2): "

set OPCAO=%ERRORLEVEL%

if "%OPCAO%"=="1" goto qwen_64k
if "%OPCAO%"=="2" goto qwen_128k
goto fim

:qwen_64k
echo.
echo ====================================================================
echo Iniciando Qwen 3.8 27B (64k Contexto, 8-bit KV, Visao Ativa)...
echo ====================================================================
llama-server.exe -m ..\models\Qwen3.8-27B-Q4_K_M.gguf --mmproj ..\models\mmproj-Qwen3.8-27B-f16.gguf -ngl 99 -fa on -c 65536 -ctk q8_0 -ctv q8_0 --port 8080 --host 0.0.0.0 -np 1
goto fim

:qwen_128k
echo.
echo ====================================================================
echo Iniciando Qwen 3.8 27B (128k Contexto Gigante, 4-bit KV Puro)...
echo ====================================================================
llama-server.exe -m ..\models\Qwen3.8-27B-Q4_K_M.gguf -ngl 99 -fa on -c 131072 -ctk q4_0 -ctv q4_0 --port 8080 --host 0.0.0.0 -np 1
goto fim

:fim
pause
