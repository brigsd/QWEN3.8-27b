@echo off
setlocal enabledelayedexpansion
title Servidor Qwen 3.8 27B (Dual GPU Llama.cpp)
cd /d "%~dp0"

echo ========================================================
echo   Configuracao Dual GPU Detectada:
echo   - GPU 0: RTX 5070 (12GB)
echo   - GPU 1: RTX 2080 Ti (11GB)
echo   - Total VRAM: 23.4 GB
echo ========================================================
echo.
echo Escolha o modo de operacao da Janela de Contexto:
echo.
echo [1] Modo Precisao (64k Tokens, 8-bit KV Cache) - Recomendado
echo     Uso de VRAM: ~20.6 GB (Folga de ~2.8 GB para o Windows)
echo.
echo [2] Modo Gigante (128k Tokens, 4-bit KV Cache) - Contexto Maximo
echo     Uso de VRAM: ~22.6 GB (Folga de ~0.8 GB)
echo.
echo [3] Modo TURBO Especulativo (64k + Draft Model 0.5B) - Maxima Velocidade
echo     Acelera a geracao para ~60 a 75 tokens/s!
echo.
choice /C 123 /N /M "Digite 1, 2 ou 3: "

if errorlevel 3 goto turbo
if errorlevel 2 goto gigante
if errorlevel 1 goto precisao

:precisao
echo.
echo Iniciando no Modo Precisao (64k Tokens, 8-bit KV)...
llama-server.exe -m ..\models\Qwen3.8-27B-Q4_K_M.gguf --mmproj ..\models\mmproj-Qwen3.8-27B-f16.gguf -ngl 99 -fa on -c 65536 -ctk q8_0 -ctv q8_0 --port 8080 --host 0.0.0.0 -np 1
goto fim

:gigante
echo.
echo Iniciando no Modo Gigante (128k Tokens, 4-bit KV)...
llama-server.exe -m ..\models\Qwen3.8-27B-Q4_K_M.gguf --mmproj ..\models\mmproj-Qwen3.8-27B-f16.gguf -ngl 99 -fa on -c 131072 -ctk q4_0 -ctv q4_0 --port 8080 --host 0.0.0.0 -np 1
goto fim

:turbo
echo.
echo Iniciando no Modo TURBO Especulativo (64k + Draft 0.5B)...
llama-server.exe -m ..\models\Qwen3.8-27B-Q4_K_M.gguf -md ..\models\qwen2.5-0.5b-instruct-q4_k_m.gguf -ngld 99 --spec-draft-n-max 4 --mmproj ..\models\mmproj-Qwen3.8-27B-f16.gguf -ngl 99 -fa on -c 65536 -ctk q8_0 -ctv q8_0 --port 8080 --host 0.0.0.0 -np 1
goto fim

:fim
pause
