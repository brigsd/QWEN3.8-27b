@echo off
title Aider CLI (Claude Code Local - llama-server)

if not "%~1"=="" (
    cd /d "%~1"
)

echo ========================================================
echo Conectando Aider ao llama-server (porta 8080)...
echo Diretorio de trabalho: %CD%
echo Idioma: Portugues / Formato: Diff Otimizado
echo ========================================================
echo DICA: Voce pode arrastar qualquer pasta de projeto para cima deste atalho!
echo.
aider --model openai/qwen3.8-27b --openai-api-base http://127.0.0.1:8080/v1 --openai-api-key none --chat-language pt --edit-format diff
pause
