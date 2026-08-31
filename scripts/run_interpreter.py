import sys
from interpreter import interpreter

# 1. Configuracoes de conexao com o llama-server local
interpreter.offline = True
interpreter.disable_telemetry = True
interpreter.llm.api_base = "http://127.0.0.1:8080/v1"
interpreter.llm.api_key = "none"
interpreter.llm.model = "openai/qwen3.8-27b"
interpreter.llm.context_window = 65536
interpreter.llm.supports_functions = False

# 2. Instrucao para forcar blocos markdown em vez de tags XML <tool_call>
interpreter.custom_instructions = (
    "To execute shell commands, file operations, or scripts on Windows, "
    "ALWAYS output standard markdown code blocks, for example:\n"
    "```powershell\n"
    "Get-ChildItem 'C:\\Users\\micro\\Desktop\\mecanifica'\n"
    "```\n"
    "or:\n"
    "```python\n"
    "print('executing')\n"
    "```\n"
    "NEVER output XML tags like <tool_call> or <function=...>. ONLY output markdown code blocks."
)

if __name__ == "__main__":
    # Inicia o chat interativo
    interpreter.chat()
