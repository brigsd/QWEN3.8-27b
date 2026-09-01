@echo off
setlocal enabledelayedexpansion
title Central de Ferramentas e Benchmarks (IA Local)
cd /d "%~dp0"

echo ====================================================================
echo   🛠️ CENTRAL DE FERRAMENTAS E UTILITARIOS - IA LOCAL
echo ====================================================================
echo.
echo [1] 📊 Testar Pontuacao e Precisao (LiveCodeBench Local)
echo [2] 🤖 Abrir Claude Code Local (Aider)
echo [3] 🩺 Rodar Diagnostico de Saude do Sistema (Doctor)
echo [4] 📥 Baixar Modelo GLM-4-9B-Chat (GGUF)
echo [5] 📥 Baixar Modelo Rascunho Qwen 0.5B (Speculative)
echo [6] 🚪 Sair
echo.
echo ====================================================================
choice /C 123456 /N /M "Selecione uma opcao (1 a 6): "

if errorlevel 6 goto fim
if errorlevel 5 goto dl_draft
if errorlevel 4 goto dl_glm
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

:dl_glm
echo.
echo Baixando GLM-4-9B-Chat Q4_K_M (~5.5 GB)...
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='THUDM/glm-4-9b-chat-GGUF', filename='glm-4-9b-chat.Q4_K_M.gguf', local_dir=r'..\models')"
echo Download concluido!
pause
goto fim

:dl_draft
echo.
powershell -ExecutionPolicy Bypass -File ..\setup\download_draft_model.ps1
pause
goto fim

:fim
