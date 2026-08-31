@echo off
title Agente Nativo Qwen 27B (Dual GPU + Ferramentas Locais)
cd /d "%~dp0\..\agent"
python agent.py
pause