"""
Agente Nativo Qwen 3.8 27B (CLI) - Supreme Edition
Dual GPU (RTX 5070 + RTX 2080 Ti) • 3 Modos de Raciocínio (Shift+Tab ou F2):
1. ⚡ NORMAL (Direto + Min-P Sampling)
2. 🧠 PENSAMENTO PROFUNDO (CoT + Scratchpad Interno)
3. 🛡️ AUTO-REFLEXÃO (Geração + Auditoria e Auto-Correção)
"""

import sys
import os
import re
import json
import requests
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Suporte UTF-8 no Windows Console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML

# Importa módulos internos
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

# Modos de Raciocínio
MODOS = ["NORMAL", "DEEP_THINK", "AUTO_REFLEXAO"]
MODO_INFO = {
    "NORMAL": {
        "nome": "⚡ NORMAL (Direto & Min-P)",
        "descricao": "Respostas rápidas e objetivas com amostragem Min-P de alta precisão.",
        "badge": "<ansigreen><b>[⚡ NORMAL]</b></ansigreen>",
        "temp": 0.2,
        "min_p": 0.05
    },
    "DEEP_THINK": {
        "nome": "🧠 PENSAMENTO PROFUNDO (CoT)",
        "descricao": "Ativa cadeia de raciocínio interna (<think>) antes de emitir a solução.",
        "badge": "<ansicyan><b>[🧠 PENSAMENTO]</b></ansicyan>",
        "temp": 0.35,
        "min_p": 0.05
    },
    "AUTO_REFLEXAO": {
        "nome": "🛡️ AUTO-REFLEXÃO (Auditoria Interna)",
        "descricao": "Gera a solução e executa uma rodada interna de auto-crítica contra falhas e bugs.",
        "badge": "<ansimagenta><b>[🛡️ REFLEXÃO]</b></ansimagenta>",
        "temp": 0.25,
        "min_p": 0.05
    }
}

modo_atual_idx = 0

PROMPT_SISTEMA_BASE = """Você é o Engenheiro de Software e Assistente de Desenvolvimento de Elite do Qwen 3.8 27B, operando diretamente na máquina do usuário via Dual GPU (RTX 5070 + RTX 2080 Ti).

Postura e Diretrizes Fundamentais:
1. ATUAÇÃO PRÁTICA E PROATIVA (Bias for Action):
   - Trate instruções de desenvolvimento (como criar funções, corrigir bugs, refatorar código) como ações práticas no disco. Localize o arquivo, aplique as mudanças com `editar_arquivo` ou `escrever_arquivo` e relate a alteração.
   - Para perguntas de arquitetura, responda de forma concisa em 2-3 parágrafos com sua recomendação técnica e os trade-offs.

2. HIERARQUIA DE BUSCA E INVESTIGAÇÃO (Sem Alucinações):
   - NUNCA invente fatos, saídas de comandos ou conteúdos de arquivos.
   - Para dúvidas sobre o projeto, use SEMPRE `buscar_relevancia` (BM25) primeiro para recuperar os trechos relevantes sem sobrecarregar a janela de contexto.
   - Use `ler_arquivo` de forma paginada para verificar a implementação exata.

3. EDIÇÃO CIRÚRGICA DE CÓDIGO:
   - Ao modificar código existente, use `editar_arquivo` com correspondência exata de `texto_antigo`.
   - Preserve rigorosamente todos os comentários, estilos, convenções e indentação do arquivo original.

4. ESTILO DE COMUNICAÇÃO:
   - Seja conciso, técnico e direto ao ponto.
   - Não narre ações desnecessárias. Execute a ferramenta silenciosamente e apresente a resposta consolidada.
   - Ao citar código ou arquivos, use a convenção navegável `caminho/arquivo.ext:linha`.
   - Responda SEMPRE em Português (PT-BR).
"""

PROMPT_THINK_EXTENSAO = """
[DIRETRIZ DE PENSAMENTO PROFUNDO (DEEP THINK)]:
Antes de responder ou executar ações no disco, elabore sua análise lógica dentro das tags `<think>` e `</think>`:
1. Decomponha o problema em partes atômicas e mapeie dependências.
2. Identifique possíveis armadilhas, casos de borda e trade-offs.
3. Formule um plano de execução passo a passo.
Após fechar `</think>`, emita a resposta e ferramentas com máxima precisão.
"""

def testar_servidor() -> bool:
    """Verifica se o servidor llama.cpp está ativo na porta 8080."""
    try:
        res = requests.get(f"{API_BASE}/models", timeout=2)
        return res.status_code == 200
    except Exception:
        return False

def obter_model_id_ativo() -> str:
    """Retorna o ID registrado pelo llama-server."""
    try:
        res = requests.get(f"{API_BASE}/models", timeout=2)
        if res.status_code == 200:
            data = res.json()
            if "data" in data and len(data["data"]) > 0:
                return data["data"][0]["id"]
    except Exception:
        pass
    return "qwen3.8-27b"

def executar_ciclo_agente(historico: List[Dict[str, Any]], modo: str = "NORMAL") -> Tuple[str, Optional[str]]:
    """Executa o loop de raciocínio com suporte ao modo selecionado."""
    headers = {"Content-Type": "application/json"}
    ferramentas_atuais = mcp_mgr.obter_ferramentas_ativas(ESQUEMA_FERRAMENTAS)
    cfg_modo = MODO_INFO[modo]
    model_id = obter_model_id_ativo()
    
    hist_local = list(historico)
    if modo == "DEEP_THINK":
        if hist_local and hist_local[0]["role"] == "system":
            hist_local[0] = {"role": "system", "content": PROMPT_SISTEMA_BASE + PROMPT_THINK_EXTENSAO}
            
    while True:
        payload = {
            "model": model_id,
            "messages": hist_local,
            "tools": ferramentas_atuais,
            "tool_choice": "auto",
            "temperature": cfg_modo["temp"],
            "min_p": cfg_modo["min_p"]
        }
        
        try:
            with console.status(f"[cyan]Qwen 27B raciocinando no modo {cfg_modo['nome']}...[/cyan]", spinner="dots"):
                res = requests.post(f"{API_BASE}/chat/completions", json=payload, headers=headers, timeout=180)
                
            if res.status_code != 200:
                console.print(f"[error]Erro do Servidor ({res.status_code}): {res.text}[/error]")
                return "Ocorreu um erro ao comunicar com o servidor Qwen 27B.", None
                
            data = res.json()
            escolha = data["choices"][0]
            mensagem = escolha["message"]
            finish_reason = escolha.get("finish_reason")
            
            hist_local.append(mensagem)
            historico.append(mensagem)
            
            # Chamada de ferramentas
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
                    mcp_handled, resultado_mcp = mcp_mgr.despachar(nome_func, args)
                    if mcp_handled:
                        resultado = resultado_mcp
                    else:
                        resultado = despachar_ferramenta(nome_func, args)
                        
                    duracao = (time.time() - t0) * 1000
                    preview = resultado.strip().split("\n")[0] if resultado else ""
                    if len(preview) > 80:
                        preview = preview[:77] + "..."
                    console.print(f"    [dim green][OK] Concluido em {duracao:.1f}ms: {preview}[/dim green]")
                    
                    msg_tool = {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": nome_func,
                        "content": resultado
                    }
                    hist_local.append(msg_tool)
                    historico.append(msg_tool)
                continue
                
            conteudo_resposta = mensagem.get("content", "")
            
            # Se for modo AUTO-REFLEXAO
            if modo == "AUTO_REFLEXAO" and len(conteudo_resposta) > 100:
                with console.status("[magenta]Qwen 27B executando Auto-Reflexão e Auditoria Interna...[/magenta]", spinner="dots"):
                    prompt_critica = (
                        "Examine criticamente a resposta/código anterior. "
                        "Identifique e corrija se houver: (1) casos de borda não tratados, (2) falhas de tipos ou concorrência, "
                        "(3) redundâncias. Apresente a versão final corrigida e aprimorada de forma limpa."
                    )
                    hist_reflexao = list(hist_local) + [
                        {"role": "user", "content": prompt_critica}
                    ]
                    payload_ref = {
                        "model": model_id,
                        "messages": hist_reflexao,
                        "temperature": 0.2,
                        "min_p": 0.05
                    }
                    res_ref = requests.post(f"{API_BASE}/chat/completions", json=payload_ref, headers=headers, timeout=120)
                    if res_ref.status_code == 200:
                        conteudo_refinado = res_ref.json()["choices"][0]["message"].get("content", "")
                        return conteudo_refinado, "Auditoria de Auto-Reflexão Aplicada"
                        
            # Extrai tags <think> se existirem
            pensamento = None
            if "<think>" in conteudo_resposta and "</think>" in conteudo_resposta:
                partes_think = conteudo_resposta.split("</think>")
                pensamento = partes_think[0].replace("<think>", "").strip()
                conteudo_resposta = partes_think[1].strip()
                
            return conteudo_resposta, pensamento
            
        except requests.exceptions.RequestException as e:
            console.print(f"[error]Erro de rede com o servidor Qwen: {e}[/error]")
            return "Falha de conexão com o servidor local.", None

def tratar_comando_barra(comando: str, historico: List[Dict[str, Any]]) -> bool:
    """Processa comandos de barra."""
    global modo_atual_idx
    cmd = comando.strip()
    partes = cmd.split(maxsplit=1)
    cmd_base = partes[0].lower()
    arg = partes[1] if len(partes) > 1 else ""
    
    # 1. ALTERNAR MODO VIA COMANDO
    if cmd_base in ("/modo", "/mode"):
        arg_lower = arg.lower()
        if "think" in arg_lower or "pensar" in arg_lower or "2" in arg_lower:
            modo_atual_idx = 1
        elif "refle" in arg_lower or "auto" in arg_lower or "3" in arg_lower:
            modo_atual_idx = 2
        else:
            modo_atual_idx = 0
            
        cfg = MODO_INFO[MODOS[modo_atual_idx]]
        console.print(Panel(
            f"• **Modo Ativo:** {cfg['nome']}\n"
            f"• **Descrição:** {cfg['descricao']}\n"
            f"• **Parâmetros:** Temperatura {cfg['temp']} | Min-P {cfg['min_p']}",
            title="[bold cyan]Modo de Raciocínio Alterado[/bold cyan]",
            border_style="cyan"
        ))
        return True

    # 2. SKILL: DOCTOR
    elif cmd_base in ("/doctor", "/diagnostico"):
        relatorio = executar_doctor(API_BASE, list(mcp_mgr.modulos_ativos))
        console.print(Panel(Markdown(relatorio), title="[bold cyan]Doctor - Diagnóstico Local[/bold cyan]", border_style="cyan"))
        return True

    # 3. SKILL: VERIFY (Testes)
    elif cmd_base in ("/verify", "/testar"):
        pasta = arg or "."
        relatorio, prompt_ia = executar_verify(pasta)
        console.print(Panel(Markdown(relatorio), title="[bold cyan]Verify - Execução de Testes[/bold cyan]", border_style="cyan"))
        if prompt_ia:
            console.print("[yellow]Acionando Qwen 27B para analisar o traceback do erro...[/yellow]")
            historico.append({"role": "user", "content": prompt_ia})
            resposta, _ = executar_ciclo_agente(historico, MODOS[modo_atual_idx])
            console.print()
            console.print(Panel(Markdown(resposta), title="[bold red]Diagnóstico de Falha (Qwen 27B)[/bold red]", border_style="red"))
        return True

    # 4. SKILL: CODE REVIEW
    elif cmd_base in ("/review", "/revisar"):
        alvo = arg or "."
        prompt_rev = obter_prompt_review(alvo)
        historico.append({"role": "user", "content": prompt_rev})
        console.print(f"[cyan]Iniciando Code Review Sênior em '{alvo}' com Qwen 27B...[/cyan]")
        resposta, _ = executar_ciclo_agente(historico, MODOS[modo_atual_idx])
        console.print()
        console.print(Panel(Markdown(resposta), title="[bold cyan]Code Review (Qwen 27B)[/bold cyan]", border_style="cyan"))
        return True

    # 5. SKILL: SECURITY REVIEW
    elif cmd_base in ("/security", "/seguranca"):
        alvo = arg or "."
        prompt_sec = obter_prompt_security(alvo)
        historico.append({"role": "user", "content": prompt_sec})
        console.print(f"[cyan]Iniciando Auditoria de Segurança OWASP em '{alvo}' com Qwen 27B...[/cyan]")
        resposta, _ = executar_ciclo_agente(historico, MODOS[modo_atual_idx])
        console.print()
        console.print(Panel(Markdown(resposta), title="[bold magenta]Auditoria de Segurança (Qwen 27B)[/bold magenta]", border_style="magenta"))
        return True

    # 6. SKILL: SIMPLIFY
    elif cmd_base in ("/simplify", "/simplificar"):
        if not arg:
            console.print("[warning]Especifique o arquivo a ser simplificado. Ex: `/simplify src/main.py`[/warning]")
            return True
        prompt_simp = obter_prompt_simplify(arg)
        historico.append({"role": "user", "content": prompt_simp})
        console.print(f"[cyan]Iniciando Refatoração e Simplificação em '{arg}' com Qwen 27B...[/cyan]")
        resposta, _ = executar_ciclo_agente(historico, MODOS[modo_atual_idx])
        console.print()
        console.print(Panel(Markdown(resposta), title="[bold green]Código Simplificado (Qwen 27B)[/bold green]", border_style="green"))
        return True

    # 7. GERENCIADOR MCP
    elif cmd_base == "/mcp":
        subpartes = arg.lower().split()
        if not subpartes or subpartes[0] in ("list", "listar", "status"):
            console.print(Panel(mcp_mgr.listar_status(), title="[bold cyan]Gerenciador MCP[/bold cyan]", border_style="cyan"))
            return True
            
        acao = subpartes[0]
        if acao == "on":
            modulo = subpartes[1] if len(subpartes) > 1 else ""
            if not modulo:
                console.print("[warning]Especifique o módulo. Ex: `/mcp on mecanifica` ou `/mcp on web`[/warning]")
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
        cfg = MODO_INFO[MODOS[modo_atual_idx]]
        ferramentas_atuais = mcp_mgr.obter_ferramentas_ativas(ESQUEMA_FERRAMENTAS)
        modulos = list(mcp_mgr.modulos_ativos) if mcp_mgr.modulos_ativos else ["Nenhum (Apenas Nativas)"]
        console.print(Panel(
            f"• **Servidor:** {API_BASE}\n"
            f"• **Modelo:** Qwen 3.8 27B Supreme (Dual GPU)\n"
            f"• **Modo de Raciocínio:** {cfg['nome']}\n"
            f"• **Módulos MCP Ativos:** {', '.join(modulos)}\n"
            f"• **Total de Ferramentas Habilitadas:** {len(ferramentas_atuais)}\n"
            f"• **Mensagens no Histórico:** {len(historico)}",
            title="[bold cyan]Status do Agente Qwen 27B[/bold cyan]",
            border_style="cyan"
        ))
        return True
        
    elif cmd_base in ("/ajuda", "/help", "/?"):
        console.print(Panel(
            "**🧠 Modos de Raciocínio & Atalhos:**\n"
            "• Pressione **[bold yellow]Shift + Tab[/bold yellow]** ou **[bold yellow]F2[/bold yellow]** para alternar modos em tempo real!\n"
            "• `/modo normal`       ➔ Modo ⚡ Rápido e Direto (Min-P 0.05)\n"
            "• `/modo think`        ➔ Modo 🧠 Pensamento Profundo (Chain of Thought)\n"
            "• `/modo reflexao`     ➔ Modo 🛡️ Auto-Reflexão e Auditoria Interna\n\n"
            "**🚀 Skills e Comandos:**\n"
            "• `/doctor`            ➔ Checkup completo do sistema (Dual GPU, VRAM, Servidor)\n"
            "• `/review <alvo>`     ➔ Auditoria e Code Review Sênior com severidade e linhas\n"
            "• `/security <alvo>`   ➔ Análise de segurança e vulnerabilidades OWASP\n"
            "• `/simplify <alvo>`   ➔ Refatoração para remover complexidade e código morto\n"
            "• `/verify [pasta]`    ➔ Executa a bateria de testes e diagnostica falhas\n"
            "• `/mcp list/on/off`   ➔ Gerencia módulos externos sem deixar resíduos\n"
            "• `/status`            ➔ Exibe saúde e ferramentas ativas\n"
            "• `/limpar`            ➔ Reseta a memória da sessão atual",
            title="[bold cyan]Menu de Skills, Modos e Comandos[/bold cyan]",
            border_style="cyan"
        ))
        return True
        
    return False

def main():
    global modo_atual_idx
    
    console.print(Panel.fit(
        "[bold cyan]🤖 Agente Nativo Qwen 3.8 27B (Supreme Intelligence Edition)[/bold cyan]\n"
        "[dim]Dual GPU (RTX 5070 + RTX 2080 Ti) • 3 Modos de Reasoning (Shift+Tab) • Skills de Elite[/dim]\n\n"
        "• Pressione [bold yellow]Shift + Tab[/bold yellow] ou [bold yellow]F2[/bold yellow] para alternar: [green]⚡ NORMAL[/green] | [cyan]🧠 PENSAMENTO[/cyan] | [magenta]🛡️ REFLEXÃO[/magenta]\n"
        "• Digite [cyan]/ajuda[/cyan] para ver todas as Skills e comandos\n"
        "• Digite [bold red]sair[/bold red] para encerrar.",
        border_style="cyan"
    ))
    
    if not testar_servidor():
        console.print(Panel(
            "[bold red][X] Servidor Qwen 27B não encontrado em http://127.0.0.1:8080[/bold red]\n\n"
            "Por favor, inicie o servidor primeiro usando o atalho:\n"
            "[yellow]1 - Iniciar Servidor Qwen 27B (Dual GPU).lnk[/yellow]",
            border_style="red"
        ))
        input("\nPressione ENTER para fechar...")
        return
        
    console.print("[success][OK] Conectado ao Servidor Qwen 3.8 27B com sucesso![/success]\n")
    
    historico = [
        {"role": "system", "content": PROMPT_SISTEMA_BASE}
    ]
    
    # Configura prompt_toolkit com KeyBindings
    kb = KeyBindings()
    
    @kb.add("s-tab")
    def _(event):
        global modo_atual_idx
        modo_atual_idx = (modo_atual_idx + 1) % len(MODOS)
        event.app.invalidate()
        
    @kb.add("f2")
    def _(event):
        global modo_atual_idx
        modo_atual_idx = (modo_atual_idx + 1) % len(MODOS)
        event.app.invalidate()
        
    session = PromptSession(key_bindings=kb)
    
    while True:
        try:
            modo_chave = MODOS[modo_atual_idx]
            cfg = MODO_INFO[modo_chave]
            prompt_html = HTML(f"{cfg['badge']} <ansicyan><b>Você &gt;</b></ansicyan> ")
            
            entrada = session.prompt(prompt_html).strip()
            
            if not entrada:
                continue
                
            if entrada.lower() in ("sair", "exit", "quit"):
                console.print("[yellow]Encerrando agente. Até logo![/yellow]")
                break
                
            if entrada.startswith("/"):
                if tratar_comando_barra(entrada, historico):
                    continue
                
            historico.append({"role": "user", "content": entrada})
            
            resposta, pensamento = executar_ciclo_agente(historico, modo_chave)
            
            console.print()
            
            # Se houver bloco de pensamento, exibe em painel dedicado
            if pensamento:
                console.print(Panel(
                    Markdown(pensamento),
                    title="[bold cyan]🧠 Cadeia de Raciocínio Interno (Thinking Process)[/bold cyan]",
                    border_style="dim cyan",
                    padding=(0, 2)
                ))
                console.print()
                
            console.print(Panel(
                Markdown(resposta),
                title=f"[bold cyan]Qwen 27B ({cfg['nome']})[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            ))
            console.print()
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Encerrando agente...[/yellow]")
            break

if __name__ == "__main__":
    main()
