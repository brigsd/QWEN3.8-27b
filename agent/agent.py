"""
Agente Nativo Qwen 27B (CLI)
Conecta-se ao llama-server local e executa ferramentas nativas com velocidade instantânea.
"""

import sys
import json
import requests
import time
from pathlib import Path
from typing import List, Dict, Any

# Garante suporte a UTF-8 no Windows Console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme

# Importa as ferramentas nativas
try:
    from tools import ESQUEMA_FERRAMENTAS, despachar_ferramenta
except ImportError:
    try:
        from agent.tools import ESQUEMA_FERRAMENTAS, despachar_ferramenta
    except ImportError:
        import tools
        ESQUEMA_FERRAMENTAS = tools.ESQUEMA_FERRAMENTAS
        despachar_ferramenta = tools.despachar_ferramenta

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "tool": "bold magenta",
    "success": "bold green"
})

console = Console(theme=custom_theme)

API_BASE = "http://127.0.0.1:8080/v1"
MODEL_NAME = "qwen3.8-27b"

PROMPT_SISTEMA = """Você é o Assistente de Engenharia e Desenvolvimento do Qwen 3.8 27B, operando diretamente no computador do usuário.
Você possui ferramentas nativas avançadas para inspecionar diretórios, ler arquivos de código/documentação, buscar símbolos, escrever e editar código, e rodar comandos no terminal.

Diretrizes Fundamentais:
1. NUNCA invente saídas ou conteúdos de arquivos. Use SEMPRE as ferramentas nativas (`ler_arquivo`, `listar_pasta`, `buscar_texto`) para verificar os fatos antes de responder.
2. Quando o usuário pedir para inspecionar uma pasta ou projeto, liste os arquivos ou leia o README relevante para entender o contexto antes de tomar decisões.
3. Responda SEMPRE em Português (PT-BR), com explicações diretas, precisas e objetivas.
4. Ao editar ou criar arquivos, mantenha a formatação e comentários originais.
"""

def testar_servidor() -> bool:
    """Verifica se o llama-server está ativo na porta 8080."""
    try:
        res = requests.get(f"{API_BASE}/models", timeout=2)
        return res.status_code == 200
    except Exception:
        return False

def executar_ciclo_agente(historico: List[Dict[str, Any]]) -> str:
    """Executa o loop de raciocínio e chamada de ferramentas até a resposta final."""
    headers = {"Content-Type": "application/json"}
    
    while True:
        payload = {
            "model": MODEL_NAME,
            "messages": historico,
            "tools": ESQUEMA_FERRAMENTAS,
            "tool_choice": "auto",
            "temperature": 0.3
        }
        
        try:
            with console.status("[cyan]Pensando...[/cyan]", spinner="dots"):
                res = requests.post(f"{API_BASE}/chat/completions", json=payload, headers=headers, timeout=120)
                
            if res.status_code != 200:
                console.print(f"[error]Erro do Servidor ({res.status_code}): {res.text}[/error]")
                return "Ocorreu um erro ao comunicar com o servidor de IA."
                
            data = res.json()
            escolha = data["choices"][0]
            mensagem = escolha["message"]
            finish_reason = escolha.get("finish_reason")
            
            # Adiciona a mensagem do assistente ao histórico
            historico.append(mensagem)
            
            # Se o modelo chamou ferramentas
            if finish_reason == "tool_calls" and "tool_calls" in mensagem:
                for tool_call in mensagem["tool_calls"]:
                    func_info = tool_call["function"]
                    nome_func = func_info["name"]
                    
                    try:
                        args = json.loads(func_info["arguments"])
                    except Exception:
                        args = {}
                        
                    args_resumo = ", ".join([f"{k}='{v}'" if isinstance(v, str) and len(v) < 40 else f"{k}={v}" for k, v in args.items()])
                    console.print(f"  [tool]>> Executando:[/tool] [bold cyan]{nome_func}[/bold cyan]({args_resumo})")
                    
                    t0 = time.time()
                    resultado = despachar_ferramenta(nome_func, args)
                    duracao = (time.time() - t0) * 1000
                    
                    # Trunca exibição longa apenas no terminal, mas envia completo para o modelo
                    preview = resultado.strip().split("\n")[0] if resultado else ""
                    if len(preview) > 80:
                        preview = preview[:77] + "..."
                    console.print(f"    [dim green][OK] Concluido em {duracao:.1f}ms: {preview}[/dim green]")
                    
                    # Adiciona a resposta da ferramenta ao histórico
                    historico.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": nome_func,
                        "content": resultado
                    })
                # Continua o loop para o modelo ler o resultado das ferramentas
                continue
                
            # Se terminou com resposta de texto
            conteudo_resposta = mensagem.get("content", "")
            return conteudo_resposta
            
        except requests.exceptions.RequestException as e:
            console.print(f"[error]Erro de rede com o llama-server: {e}[/error]")
            return "Falha de conexão com o servidor local."

def main():
    console.print(Panel.fit(
        "[bold cyan]Agente Nativo Qwen 3.8 27B[/bold cyan]\n"
        "[dim]Aceleracao Dual GPU • Ferramentas Nativas • 100% Local[/dim]\n\n"
        "• Digite seu pedido em linguagem natural (ex: [yellow]leia o readme da pasta X[/yellow])\n"
        "• Digite [bold red]sair[/bold red] ou [bold red]exit[/bold red] para encerrar.",
        border_style="cyan"
    ))
    
    if not testar_servidor():
        console.print(Panel(
            "[bold red][X] Servidor llama.cpp nao encontrado em http://127.0.0.1:8080[/bold red]\n\n"
            "Por favor, inicie o servidor primeiro usando o atalho:\n"
            "[yellow]1 - Iniciar Servidor Qwen 27B.lnk[/yellow]",
            border_style="red"
        ))
        input("\nPressione ENTER para fechar...")
        return
        
    console.print("[success][OK] Conectado ao Servidor Qwen 3.8 27B com sucesso![/success]\n")
    
    historico = [
        {"role": "system", "content": PROMPT_SISTEMA}
    ]
    
    while True:
        try:
            console.print("[bold cyan]Voce >[/bold cyan] ", end="")
            entrada = input().strip()
            
            if not entrada:
                continue
                
            if entrada.lower() in ("sair", "exit", "quit"):
                console.print("[yellow]Encerrando agente. Ate logo![/yellow]")
                break
                
            if entrada.lower() == "limpar":
                historico = [{"role": "system", "content": PROMPT_SISTEMA}]
                console.clear()
                console.print("[green]Historico limpo com sucesso![/green]")
                continue
                
            historico.append({"role": "user", "content": entrada})
            
            resposta = executar_ciclo_agente(historico)
            
            console.print()
            console.print(Panel(
                Markdown(resposta),
                title="[bold cyan]Qwen 27B[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            ))
            console.print()
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Encerrando agente...[/yellow]")
            break

if __name__ == "__main__":
    main()
