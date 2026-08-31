import sys
from interpreter import interpreter

# 1. Modo 100% Autonomo e Otimizacoes de Terminal
interpreter.auto_run = True                  # Executa automaticamente sem pedir permissao (y/n)
interpreter.max_output = 50000               # Permite ler arquivos grandes sem truncar
interpreter.no_highlight_active_line = True  # Evita repeticoes de texto no terminal do Windows
interpreter.offline = True
interpreter.disable_telemetry = True

# 2. Configuracoes do modelo local
interpreter.llm.api_base = "http://127.0.0.1:8080/v1"
interpreter.llm.api_key = "none"
interpreter.llm.model = "openai/qwen3.8-27b"
interpreter.llm.context_window = 65536
interpreter.llm.supports_functions = False

# 3. Instrucoes do Sistema para execucao limpa
interpreter.custom_instructions = (
    "You are an autonomous AI assistant with full permissions on Windows.\n"
    "To read, write, search, or inspect files and directories, write Python code blocks (```python ... ```).\n"
    "For reading files, ALWAYS use Python with UTF-8 encoding, e.g.:\n"
    "```python\n"
    "with open(r'C:\\path\\file.txt', 'r', encoding='utf-8') as f:\n"
    "    print(f.read())\n"
    "```\n"
    "For directory listing, use `os.listdir()` or `pathlib.Path.glob()`.\n"
    "Python executes cleanly and avoids shell terminal echoing on Windows.\n"
    "NEVER output XML tags like <tool_call> or <function=...>. ONLY output markdown code blocks."
)

if __name__ == "__main__":
    interpreter.chat()
