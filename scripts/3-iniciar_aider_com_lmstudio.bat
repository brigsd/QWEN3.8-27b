@echo off
title Aider CLI (Claude Code Local - LM Studio)

if not "%~1"=="" (
    cd /d "%~1"
)

echo ========================================================
echo Conectando Aider ao LM Studio (porta 1234)...
echo Diretorio de trabalho: %CD%
echo Certifique-se de que o LM Studio esta com o servidor ligado!
echo ========================================================
echo DICA: Voce pode arrastar qualquer pasta de projeto para cima deste arquivo .bat!
echo.
aider --model openai/qwen3.8-27b --openai-api-base http://127.0.0.1:1234/v1 --openai-api-key none
pause
