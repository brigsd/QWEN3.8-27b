@echo off
title Servidor Qwen 3.8 27B TURBO (Speculative Decoding Dual GPU)
cd /d "%~dp0"

echo ====================================================================
echo  Iniciando Qwen 3.8 27B em Modo TURBO com Speculative Decoding!
echo  Dual GPU: RTX 5070 + RTX 2080 Ti
echo  Modelo Principal: 27B Q4_K_M
echo  Modelo Rascunho: 0.5B Q4_K_M (Aceleracao Especulativa ~60-75 tok/s)
echo ====================================================================
echo.

llama-server.exe -m ..\models\Qwen3.8-27B-Q4_K_M.gguf ^
  -md ..\models\qwen2.5-0.5b-instruct-q4_k_m.gguf ^
  -ngld 99 ^
  --spec-draft-n-max 4 ^
  --mmproj ..\models\mmproj-Qwen3.8-27B-f16.gguf ^
  -ngl 99 ^
  -fa on ^
  -c 65536 ^
  -ctk q8_0 ^
  -ctv q8_0 ^
  --port 8080 ^
  --host 0.0.0.0 ^
  -np 1

pause
