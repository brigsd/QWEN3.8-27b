@echo off
title Agente com Acesso ao PC (Open Interpreter + Qwen 27B)
cd /d "%~dp0"
echo ========================================================
echo Conectando Open Interpreter ao llama-server (porta 8080)...
echo [MODO AGENTE ATIVO] Acesso total a CMD, PowerShell e Arquivos!
echo ========================================================
echo.
python run_interpreter.py
pause
