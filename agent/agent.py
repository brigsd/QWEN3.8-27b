"""
Agente Nativo Qwen 27B (CLI)
Conecta-se ao llama-server local com Tool Calling Nativo, Motor BM25 e Gerenciador Dinâmico de MCP (/mcp).
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

# Importa ferramentas nativas e MCP Manager
try:
    from tools import ESQUEMA_FERRAMENTAS, despachar_ferramenta
    from mcp_manager import MCPManager
except ImportError:
    try:
        from agent.tools import ESQUEMA_FERRAMENTAS, despachar_ferramenta
        from agent.mcp_manager import MCPManager
    except ImportError:
        import tools
        from mcp_manager import MCPManager
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
mcp_mgr = MCPManager()

API_BASE = "http://127.0.0.1:8080/v1"
MODEL_NAME = "qwen3.8-27b"

PROMPT_SISTEMA_BASE = """Você é o Assistente de Engenharia e Desenvolvimento do Qwen 3.8 27B, operando diretamente no computador do usuário.
Você possui ferramentas nativas avançadas para inspecionar diretórios, buscar relevância via BM25, ler arquivos de código/documentação, escrever e editar código, e rodar comandos no terminal.

Diretrizes Fundamentais:
1. NUNCA invente saídas ou conteúdos de arquivos. Use SEMPRE as ferramentas nativas (`buscar_relevancia`, `ler_arquivo`, `listar_pasta`, `buscar_texto`) para verificar os fatos antes de responder.
2. Para perguntas conceituais ou dúvidas sobre o projeto, use `buscar_relevancia` para localizar rapidamente os documentos mais pertinentes antes de ler arquivos inteiros.
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
    
    # Obtem schemas apenas das ferramentas atualmente ativas
    ferramentas_atuais = mcp_mgr.obter_ferramentas_ativas(ESQUEMA_FERRAMENTAS)
    
    while True:
        payload = {
            "model": MODEL_NAME,
            "messages": historico,
            "tools": ferramentas_atuais,
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
                    
                    # 1. Tenta despachar pelo MCP Manager se for uma ferramenta MCP ativa
                    mcp_handled, resultado_mcp = mcp_mgr.despachar(nome_func, args)
                    if mcp_handled:
                        resultado = resultado_mcp
                    else:
                        # 2. Despacha pelas ferramentas nativas
                        resultado = despachar_ferramenta(nome_func, args)
                        
                    duracao = (time.time() - t0) * 1000
                    
                    # Preview no terminal
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

def tratar_comando_barra(comando: str, historico: List[Dict[str, Any]]) -> bool:
    """Processa comandos de barra (/mcp, /limpar, /status, /ajuda). Retorna True se foi tratado."""
    cmd = comando.strip().lower()
    partes = cmd.split()
    cmd_base = partes[0]
    
    if cmd_base == "/mcp":
        if len(partes) == 1 or partes[1] in ("list", "listar", "status"):
            console.print(Panel(mcp_mgr.listar_status(), title="[bold cyan]Gerenciador MCP[/bold cyan]", border_style="cyan"))
            return True
            
        acao = partes[1]
        if acao == "on":
            modulo = partes[2] if len(partes) > 2 else ""
            if not modulo:
                console.print("[warning]Especifique o módulo. Ex: `/mcp on mecanifica` ou `/mcp on web` ou `/mcp on all`[/warning]")
            else:
                ok, msg = mcp_mgr.ativar(modulo)
                console.print(f"[{'success' if ok else 'error'}]{msg}[/{'success' if ok else 'error'}]")
            return True
            
        elif acao == "off":
            modulo = partes[2] if len(partes) > 2 else ""
            ok, msg = mcp_mgr.desativar(modulo)
            console.print(f"[success]{msg}[/success]")
            return True
        else:
            console.print("[warning]Uso do comando /mcp: `/mcp list`, `/mcp on <nome>`, `/mcp off [nome]`[/warning]")
            return True
            
    elif cmd_base in ("/limpar", "/clear"):
        historico.clear()
        historico.append({"role": "system", "content": PROMPT_SISTEMA_BASE})
        console.clear()
        console.print("[green]Histórico de conversa limpo com sucesso![/green]")
        return True
        
    elif cmd_base in ("/status", "/info"):
        ferramentas_atuais = mcp_mgr.obter_ferramentas_ativas(ESQUEMA_FERRAMENTAS)
        modulos = list(mcp_mgr.modulos_ativos) if mcp_mgr.modulos_ativos else ["Nenhum (Apenas Nativas)"]
        console.print(Panel(
            f"• **Servidor:** {API_BASE}\n"
            f"• **Modelo:** {MODEL_NAME}\n"
            f"• **Módulos MCP Ativos:** {', '.join(modulos)}\n"
            f"• **Total de Ferramentas Habilitadas:** {len(ferramentas_atuais)}\n"
            f"• **Mensagens no Histórico:** {len(historico)}",
            title="[bold cyan]Status do Agente[/bold cyan]",
            border_style="cyan"
        ))
        return True
        
    elif cmd_base in ("/ajuda", "/help", "/?"):
        console.print(Panel(
            "**Comandos Rápidos Disponíveis:**\n\n"
            "• `/mcp list`        ➔ Lista os módulos MCP disponíveis e ativos\n"
            "• `/mcp on <nome>`   ➔ Ativa um módulo MCP (ex: `/mcp on mecanifica` ou `/mcp on web`)\n"
            "• `/mcp off [nome]`  ➔ Desativa um módulo ou todos (`/mcp off`)\n"
            "• `/status`          ➔ Mostra ferramentas ativas e contagem de contexto\n"
            "• `/limpar`          ➔ Reseta a memória da conversa atual\n"
            "• `sair` ou `exit`   ➔ Fecha o agente",
            title="[bold cyan]Ajuda e Comandos[/bold cyan]",
            border_style="cyan"
        ))
        return True
        
    return False

def main():
    console.print(Panel.fit(
        "[bold cyan]🤖 Agente Nativo Qwen 3.8 27B[/bold cyan]\n"
        "[dim]Aceleração Dual GPU • Ferramentas Nativas • Suporte a MCP Dinâmico (/mcp)[/dim]\n\n"
        "• Digite seu pedido em linguagem natural (ex: [yellow]leia o readme da pasta X[/yellow])\n"
        "• Digite [cyan]/mcp[/cyan] para gerenciar extensões (Mecanifica, Web, etc.)\n"
        "• Digite [bold red]sair[/bold red] para encerrar.",
        border_style="cyan"
    ))
    
    if not testar_servidor():
        console.print(Panel(
            "[bold red][X] Servidor llama.cpp não encontrado em http://127.0.0.1:8080[/bold red]\n\n"
            "Por favor, inicie o servidor primeiro usando o atalho:\n"
            "[yellow]1 - Iniciar Servidor Qwen 27B.lnk[/yellow]",
            border_style="red"
        ))
        input("\nPressione ENTER para fechar...")
        return
        
    console.print("[success][OK] Conectado ao Servidor Qwen 3.8 27B com sucesso![/success]\n")
    
    historico = [
        {"role": "system", "content": PROMPT_SISTEMA_BASE}
    ]
    
    while True:
        try:
            console.print("[bold cyan]Você >[/bold cyan] ", end="")
            entrada = input().strip()
            
            if not entrada:
                continue
                
            if entrada.lower() in ("sair", "exit", "quit"):
                console.print("[yellow]Encerrando agente. Até logo![/yellow]")
                break
                
            # Verifica se é um comando de barra (/mcp, /status, /limpar, /ajuda)
            if entrada.startswith("/"):
                if tratar_comando_barra(entrada, historico):
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
