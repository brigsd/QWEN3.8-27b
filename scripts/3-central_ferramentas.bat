@echo off
setlocal enabledelayedexpansion
title Central de Ferramentas e Benchmarks (IA Local)
cd /d "%~dp0"

cls
echo ====================================================================
echo   CENTRAL DE FERRAMENTAS E UTILITARIOS - IA LOCAL
echo ====================================================================
echo.
echo [1] Testar Pontuacao e Precisao (LiveCodeBench Local)
echo [2] Abrir Claude Code Local (Aider)
echo [3] Rodar Diagnostico de Saude do Sistema (Doctor)
echo [4] Abrir Chat Web no Navegador (Interface Grafica no Chrome/Edge)
echo [5] Sair
echo.
echo ====================================================================
choice /C 12345 /N /M "Selecione uma opcao (1 a 5): "

if errorlevel 5 goto fim
if errorlevel 4 goto web_chat
if errorlevel 3 goto doctor
if errorlevel 2 goto aider
if errorlevel 1 goto bench

:bench
echo.
python eval_benchmark.py
pause
goto fim

:aider
echo.
call 2-iniciar_aider_com_llama.bat
goto fim

:doctor
echo.
python -c "import sys; sys.path.append(r'..\agent'); from skills import executar_doctor; print(executar_doctor('http://127.0.0.1:8080/v1', []))"
pause
goto fim

:web_chat
echo.
echo Abrindo Interface Web no seu Navegador...
start "" "%~dp0web_chat.html"
goto fim

:fim
