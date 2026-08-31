@echo off
title Benchmark de Precisao Qwen 3.8 27B Local
cd /d "%~dp0"

echo ========================================================
echo   Executando Bateria de Avaliacao de Precisao (Leaderboard)
echo ========================================================
echo.
python eval_benchmark.py
pause
