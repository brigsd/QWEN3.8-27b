"""
Agente Nativo Qwen 27B (CLI)
Conecta-se ao llama-server local com Tool Calling Nativo, Motor BM25, MCP Dinâmico (/mcp) e Skills de Elite (/doctor, /review, /security, /simplify, /verify).
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

# Importa ferramentas nativas, MCP Manager e Skills
try:
    from tools import ESQUEMA_FERRAMENTAS, despachar_ferramenta
    from mcp_manager import MCPManager
    from skills import executar_doctor, obter_prompt_review, obter_prompt_security, obter_prompt_simplify, executar_verify
except ImportError:
    try:
        from agent.tools import ESQUEMA_FERRAMENTAS, despachar_ferramenta
        from agent.mcp_manager import MCPManager
        from agent.skills import executar_doctor, obter_prompt_review, obter_prompt_security, obter_prompt_simplify, executar_verify
    except ImportError:
        import tools
        from mcp_manager import MCPManager
        from skills import executar_doctor, obter_prompt_review, obter_prompt_security, obter_prompt_simplify, executar_verify
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

# Prompt de Sistema inspirado nas diretrizes do Claude Code, Antigravity e Cursor
PROMPT_SISTEMA_BASE = """Você é o Engenheiro de Software e Assistente de Desenvolvimento de Elite do Qwen 3.8 27B, operando diretamente no computador do usuário.

Postura e Diretrizes Operacionais Fundamentais:
1. ATUAÇÃO PRÁTICA E PROATIVA (Bias for Action):
   - Trate instruções de desenvolvimento (como criar funções, corrigir bugs, refatorar código) como ações práticas no disco. Localize o arquivo, aplique as mudanças cirúrgicas com `editar_arquivo` ou `escrever_arquivo` e relate a alteração.
   - Para perguntas exploratórias ou de arquitetura ("como podemos fazer X?"), responda de forma concisa em 2-3 parágrafos com sua recomendação técnica e os principais trade-offs antes de implementar.

2. HIERARQUIA DE BUSCA E INVESTIGAÇÃO (Sem Alucinações):
   - NUNCA invente fatos, saídas de comandos ou conteúdos de arquivos.
   - Para entender o contexto de um projeto ou responder dúvidas conceituais, use SEMPRE `buscar_relevancia` (BM25) primeiro para recuperar os trechos relevantes sem sobrecarregar a janela de contexto.
   - Use `ler_arquivo` de forma paginada para verificar a implementação exata.

3. EDIÇÃO CIRÚRGICA DE CÓDIGO:
   - Ao modificar código existente, use `editar_arquivo` com correspondência exata de `texto_antigo`.
   - Preserve rigorosamente todos os comentários, estilos, convenções e indentação do arquivo original.

4. MEMÓRIA PERSISTENTE E APRENDIZADOS:
   - Use `consultar_memoria` quando precisar recuperar decisões e convenções arquiteturais salvas em sessões passadas.
   - Use `salvar_memoria` quando o usuário definir regras importantes ou preferências para o projeto.

5. ESTILO DE COMUNICAÇÃO:
   - Seja conciso, técnico e direto ao ponto.
   - Não narre ações desnecessárias ("Vou abrir o arquivo..."). Execute a ferramenta silenciosamente e apresente a resposta consolidada.
   - Ao citar código ou arquivos, use a convenção navegável `caminho/arquivo.ext:linha`.
   - Responda SEMPRE em Português (PT-BR).
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
    ferramentas_atuais = mcp_mgr.obter_ferramentas_ativas(ESQUEMA_FERRAMENTAS)
    
    while True:
        payload = {
            "model": MODEL_NAME,
            "messages": historico,
            "tools": ferramentas_atuais,
            "tool_choice": "auto",
            "temperature": 0.2
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
                    
                    # 1. Despacho MCP
                    mcp_handled, resultado_mcp = mcp_mgr.despachar(nome_func, args)
                    if mcp_handled:
                        resultado = resultado_mcp
                    else:
                        # 2. Despacho Nativo
                        resultado = despachar_ferramenta(nome_func, args)
                        
                    duracao = (time.time() - t0) * 1000
                    preview = resultado.strip().split("\n")[0] if resultado else ""
                    if len(preview) > 80:
                        preview = preview[:77] + "..."
                    console.print(f"    [dim green][OK] Concluido em {duracao:.1f}ms: {preview}[/dim green]")
                    
                    historico.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": nome_func,
                        "content": resultado
                    })
                continue
                
            conteudo_resposta = mensagem.get("content", "")
            return conteudo_resposta
            
        except requests.exceptions.RequestException as e:
            console.print(f"[error]Erro de rede com o llama-server: {e}[/error]")
            return "Falha de conexão com o servidor local."

def tratar_comando_barra(comando: str, historico: List[Dict[str, Any]]) -> bool:
    """Processa comandos de barra (/doctor, /review, /security, /simplify, /verify, /mcp, /limpar, /status, /ajuda)."""
    cmd = comando.strip()
    partes = cmd.split(maxsplit=1)
    cmd_base = partes[0].lower()
    arg = partes[1] if len(partes) > 1 else ""
    
    # 1. SKILL: DOCTOR
    if cmd_base in ("/doctor", "/diagnostico"):
        relatorio = executar_doctor(API_BASE, list(mcp_mgr.modulos_ativos))
        console.print(Panel(Markdown(relatorio), title="[bold cyan]Doctor - Diagnóstico Local[/bold cyan]", border_style="cyan"))
        return True

    # 2. SKILL: VERIFY (Testes)
    elif cmd_base in ("/verify", "/testar"):
        pasta = arg or "."
        relatorio, prompt_ia = executar_verify(pasta)
        console.print(Panel(Markdown(relatorio), title="[bold cyan]Verify - Execução de Testes[/bold cyan]", border_style="cyan"))
        if prompt_ia:
            console.print("[yellow]Acionando Qwen 27B para analisar o traceback do erro...[/yellow]")
            historico.append({"role": "user", "content": prompt_ia})
            resposta = executar_ciclo_agente(historico)
            console.print()
            console.print(Panel(Markdown(resposta), title="[bold red]Diagnóstico de Falha (Qwen 27B)[/bold red]", border_style="red"))
        return True

    # 3. SKILL: CODE REVIEW
    elif cmd_base in ("/review", "/revisar"):
        alvo = arg or "."
        prompt_rev = obter_prompt_review(alvo)
        historico.append({"role": "user", "content": prompt_rev})
        console.print(f"[cyan]Iniciando Code Review Sênior em '{alvo}'...[/cyan]")
        resposta = executar_ciclo_agente(historico)
        console.print()
        console.print(Panel(Markdown(resposta), title="[bold cyan]Code Review (Qwen 27B)[/bold cyan]", border_style="cyan"))
        return True

    # 4. SKILL: SECURITY REVIEW
    elif cmd_base in ("/security", "/seguranca"):
        alvo = arg or "."
        prompt_sec = obter_prompt_security(alvo)
        historico.append({"role": "user", "content": prompt_sec})
        console.print(f"[cyan]Iniciando Auditoria de Segurança OWASP em '{alvo}'...[/cyan]")
        resposta = executar_ciclo_agente(historico)
        console.print()
        console.print(Panel(Markdown(resposta), title="[bold magenta]Auditoria de Segurança (Qwen 27B)[/bold magenta]", border_style="magenta"))
        return True

    # 5. SKILL: SIMPLIFY
    elif cmd_base in ("/simplify", "/simplificar"):
        if not arg:
            console.print("[warning]Especifique o arquivo a ser simplificado. Ex: `/simplify src/main.py`[/warning]")
            return True
        prompt_simp = obter_prompt_simplify(arg)
        historico.append({"role": "user", "content": prompt_simp})
        console.print(f"[cyan]Iniciando Refatoração e Simplificação em '{arg}'...[/cyan]")
        resposta = executar_ciclo_agente(historico)
        console.print()
        console.print(Panel(Markdown(resposta), title="[bold green]Código Simplificado (Qwen 27B)[/bold green]", border_style="green"))
        return True

    # 6. GERENCIADOR MCP
    elif cmd_base == "/mcp":
        subpartes = arg.lower().split()
        if not subpartes or subpartes[0] in ("list", "listar", "status"):
            console.print(Panel(mcp_mgr.listar_status(), title="[bold cyan]Gerenciador MCP[/bold cyan]", border_style="cyan"))
            return True
            
        acao = subpartes[0]
        if acao == "on":
            modulo = subpartes[1] if len(subpartes) > 1 else ""
            if not modulo:
                console.print("[warning]Especifique o módulo. Ex: `/mcp on mecanifica` ou `/mcp on web` ou `/mcp on all`[/warning]")
            else:
                ok, msg = mcp_mgr.ativar(modulo)
                console.print(f"[{'success' if ok else 'error'}]{msg}[/{'success' if ok else 'error'}]")
            return True
            
        elif acao == "off":
            modulo = subpartes[1] if len(subpartes) > 1 else ""
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
            "**🚀 Skills e Comandos Rápidos do Agente:**\n\n"
            "• `/doctor`            ➔ Checkup completo do sistema (Dual GPU, VRAM, Servidor, Disco)\n"
            "• `/review <alvo>`     ➔ Auditoria e Code Review Sênior com severidade e linhas\n"
            "• `/security <alvo>`   ➔ Análise estrita de segurança e vulnerabilidades OWASP\n"
            "• `/simplify <alvo>`   ➔ Refatoração para remover complexidade e código morto\n"
            "• `/verify [pasta]`    ➔ Executa a bateria de testes e diagnostica falhas\n"
            "• `/mcp list/on/off`   ➔ Gerencia módulos externos sem deixar resíduos\n"
            "• `/status`            ➔ Exibe saúde e ferramentas ativas\n"
            "• `/limpar`            ➔ Reseta a memória da sessão atual\n"
            "• `sair` ou `exit`     ➔ Encerra o agente",
            title="[bold cyan]Menu de Skills e Comandos[/bold cyan]",
            border_style="cyan"
        ))
        return True
        
    return False

def main():
    console.print(Panel.fit(
        "[bold cyan]🤖 Agente Nativo Qwen 3.8 27B (Skills Edition)[/bold cyan]\n"
        "[dim]Dual GPU • Skills (/doctor, /review, /security, /simplify, /verify) • MCP Dinâmico[/dim]\n\n"
        "• Digite seu pedido em linguagem natural (ex: [yellow]leia o readme da pasta X[/yellow])\n"
        "• Digite [cyan]/ajuda[/cyan] para ver as novas Skills disponíveis\n"
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
