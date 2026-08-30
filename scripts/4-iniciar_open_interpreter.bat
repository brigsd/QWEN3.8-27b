@echo off
title Agente com Acesso ao PC (Open Interpreter + Qwen 27B)
echo ========================================================
echo Conectando Open Interpreter ao llama-server (porta 8080)...
echo [MODO AGENTE ATIVO] Acesso total a CMD, PowerShell e Arquivos!
echo ========================================================
echo.
interpreter --api_base http://127.0.0.1:8080/v1 --api_key none --model openai/qwen3.8-27b --context_window 65536
pause
