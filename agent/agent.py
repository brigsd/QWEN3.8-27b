"""
Agente Nativo Universal (CLI) - Supreme Edition
Compatível com Qwen 3.8 27B e GLM-5.3-Flash (321B)
Auto-descoberta dinâmica de modelo e suporte a 3 Modos de Raciocínio (Shift+Tab):
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
MODEL_NAME = "default"
MODEL_DISPLAY = "IA Local"
FERRAMENTAS_HABILITADAS = True

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

def obter_modelo_ativo() -> Tuple[str, str]:
    """Descobre dinamicamente qual modelo está rodando no servidor na porta 8080."""
    global MODEL_NAME, MODEL_DISPLAY
    try:
        res = requests.get(f"{API_BASE}/models", timeout=3)
        if res.status_code == 200:
            data = res.json()
            if "data" in data and len(data["data"]) > 0:
                mid = data["data"][0]["id"]
                MODEL_NAME = mid
                if "glm" in mid.lower():
                    MODEL_DISPLAY = "GLM-5.3-Flash (321B MoE)"
                elif "qwen" in mid.lower():
                    MODEL_DISPLAY = "Qwen 3.8 27B"
                else:
                    MODEL_DISPLAY = mid.upper()
                return MODEL_NAME, MODEL_DISPLAY
    except Exception:
        pass
    return "qwen3.8-27b", "Qwen 3.8 27B"

def gerar_prompt_sistema(nome_modelo: str, is_glm: bool = False) -> str:
    if is_glm:
        # Para o GLM-5.3 (Streaming de SSD), usamos um prompt ultraleve para prefill instantâneo
        return "Você é um assistente especialista de inteligência artificial. Responda com precisão, clareza e em Português do Brasil."
        
    return f"""Você é o Engenheiro de Software e Assistente de Desenvolvimento de Elite operando com o modelo {nome_modelo} diretamente no computador do usuário.

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
   - Responda SEMPRE em Português (PT-BR).
"""

PROMPT_THINK_EXTENSAO = """
[DIRETRIZ DE PENSAMENTO PROFUNDO (DEEP THINK)]:
Antes de responder, elabore sua análise lógica dentro das tags `<think>` e `</think>`:
1. Decomponha o problema em partes atômicas e mapeie dependências.
2. Identifique possíveis armadilhas, casos de borda e trade-offs.
Após fechar `</think>`, emita a resposta com máxima precisão.
"""

def testar_servidor() -> bool:
    """Verifica se o servidor está ativo na porta 8080."""
    try:
        res = requests.get(f"{API_BASE}/models", timeout=3)
        return res.status_code == 200
    except Exception:
        return False

def executar_ciclo_agente(historico: List[Dict[str, Any]], modo: str = "NORMAL") -> Tuple[str, Optional[str]]:
    """Executa o loop de raciocínio com suporte ao modo selecionado."""
    global FERRAMENTAS_HABILITADAS
    headers = {"Content-Type": "application/json"}
    
    mid, mdisp = obter_modelo_ativo()
    is_glm = "glm" in mid.lower()
    cfg_modo = MODO_INFO[modo]
    
    # Se for GLM, enviamos ferramentas apenas se o usuário tiver ativado ou não for chat puro
    if is_glm and not FERRAMENTAS_HABILITADAS:
        ferramentas_atuais = None
    else:
        ferramentas_atuais = mcp_mgr.obter_ferramentas_ativas(ESQUEMA_FERRAMENTAS)
    
    hist_local = list(historico)
    if modo == "DEEP_THINK":
        if hist_local and hist_local[0]["role"] == "system":
            hist_local[0] = {"role": "system", "content": gerar_prompt_sistema(mdisp, is_glm) + PROMPT_THINK_EXTENSAO}
            
    while True:
        payload = {
            "model": mid,
            "messages": hist_local,
            "temperature": cfg_modo["temp"],
            "min_p": cfg_modo["min_p"]
        }
        
        if ferramentas_atuais:
            payload["tools"] = ferramentas_atuais
            payload["tool_choice"] = "auto"
            
        timeout_req = 600 if is_glm else 240
        
        try:
            with console.status(f"[cyan]{mdisp} processando no modo {cfg_modo['nome']}...[/cyan]", spinner="dots"):
                res = requests.post(f"{API_BASE}/chat/completions", json=payload, headers=headers, timeout=timeout_req)
                
            if res.status_code != 200:
                console.print(f"[error]Erro do Servidor ({res.status_code}): {res.text}[/error]")
                return "Ocorreu um erro ao comunicar com o servidor de IA.", None
                
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
            if modo == "AUTO_REFLEXAO" and len(conteudo_resposta) > 100 and not is_glm:
                with console.status(f"[magenta]{mdisp} executando Auto-Reflexão e Auditoria...[/magenta]", spinner="dots"):
                    prompt_critica = (
                        "Examine criticamente a resposta/código anterior. "
                        "Identifique e corrija se houver casos de borda ou bugs. Apresente a versão final corrigida."
                    )
                    hist_reflexao = list(hist_local) + [
                        {"role": "user", "content": prompt_critica}
                    ]
                    payload_ref = {
                        "model": mid,
                        "messages": hist_reflexao,
                        "temperature": 0.2,
                        "min_p": 0.05
                    }
                    res_ref = requests.post(f"{API_BASE}/chat/completions", json=payload_ref, headers=headers, timeout=180)
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
            console.print(f"[error]Erro de rede com o servidor: {e}[/error]")
            return "Falha de conexão com o servidor local.", None

def tratar_comando_barra(comando: str, historico: List[Dict[str, Any]]) -> bool:
    """Processa comandos de barra."""
    global modo_atual_idx, FERRAMENTAS_HABILITADAS
    cmd = comando.strip()
    partes = cmd.split(maxsplit=1)
    cmd_base = partes[0].lower()
    arg = partes[1] if len(partes) > 1 else ""
    
    # ALTERNAR TOOLS ON/OFF
    if cmd_base in ("/tools", "/tool", "/ferramentas"):
        if arg.lower() == "off":
            FERRAMENTAS_HABILITADAS = False
            console.print("[yellow]Ferramentas em disco desabilitadas (Modo Conversa Rápida).[/yellow]")
        elif arg.lower() == "on":
            FERRAMENTAS_HABILITADAS = True
            console.print("[green]Ferramentas em disco habilitadas (Modo Programador Ativo).[/green]")
        else:
            status = "HABILITADAS" if FERRAMENTAS_HABILITADAS else "DESABILITADAS"
            console.print(f"Status das Ferramentas: **{status}** (Use `/tools on` ou `/tools off`)")
        return True

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
            _, mdisp = obter_modelo_ativo()
            console.print(f"[yellow]Acionando {mdisp} para analisar o traceback do erro...[/yellow]")
            historico.append({"role": "user", "content": prompt_ia})
            resposta, _ = executar_ciclo_agente(historico, MODOS[modo_atual_idx])
            console.print()
            console.print(Panel(Markdown(resposta), title=f"[bold red]Diagnóstico de Falha ({mdisp})[/bold red]", border_style="red"))
        return True

    # 4. SKILL: CODE REVIEW
    elif cmd_base in ("/review", "/revisar"):
        alvo = arg or "."
        prompt_rev = obter_prompt_review(alvo)
        historico.append({"role": "user", "content": prompt_rev})
        _, mdisp = obter_modelo_ativo()
        console.print(f"[cyan]Iniciando Code Review Sênior em '{alvo}' com {mdisp}...[/cyan]")
        resposta, _ = executar_ciclo_agente(historico, MODOS[modo_atual_idx])
        console.print()
        console.print(Panel(Markdown(resposta), title=f"[bold cyan]Code Review ({mdisp})[/bold cyan]", border_style="cyan"))
        return True

    # 5. SKILL: SECURITY REVIEW
    elif cmd_base in ("/security", "/seguranca"):
        alvo = arg or "."
        prompt_sec = obter_prompt_security(alvo)
        historico.append({"role": "user", "content": prompt_sec})
        _, mdisp = obter_modelo_ativo()
        console.print(f"[cyan]Iniciando Auditoria de Segurança OWASP em '{alvo}' com {mdisp}...[/cyan]")
        resposta, _ = executar_ciclo_agente(historico, MODOS[modo_atual_idx])
        console.print()
        console.print(Panel(Markdown(resposta), title=f"[bold magenta]Auditoria de Segurança ({mdisp})[/bold magenta]", border_style="magenta"))
        return True

    # 6. SKILL: SIMPLIFY
    elif cmd_base in ("/simplify", "/simplificar"):
        if not arg:
            console.print("[warning]Especifique o arquivo a ser simplificado. Ex: `/simplify src/main.py`[/warning]")
            return True
        prompt_simp = obter_prompt_simplify(arg)
        historico.append({"role": "user", "content": prompt_simp})
        _, mdisp = obter_modelo_ativo()
        console.print(f"[cyan]Iniciando Refatoração e Simplificação em '{arg}' com {mdisp}...[/cyan]")
        resposta, _ = executar_ciclo_agente(historico, MODOS[modo_atual_idx])
        console.print()
        console.print(Panel(Markdown(resposta), title=f"[bold green]Código Simplificado ({mdisp})[/bold green]", border_style="green"))
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
        mid, mdisp = obter_modelo_ativo()
        is_glm = "glm" in mid.lower()
        historico.clear()
        historico.append({"role": "system", "content": gerar_prompt_sistema(mdisp, is_glm)})
        console.clear()
        console.print("[green]Histórico de conversa limpo com sucesso![/green]")
        return True
        
    elif cmd_base in ("/status", "/info"):
        cfg = MODO_INFO[MODOS[modo_atual_idx]]
        mid, mdisp = obter_modelo_ativo()
        ferramentas_atuais = mcp_mgr.obter_ferramentas_ativas(ESQUEMA_FERRAMENTAS)
        modulos = list(mcp_mgr.modulos_ativos) if mcp_mgr.modulos_ativos else ["Nenhum (Apenas Nativas)"]
        console.print(Panel(
            f"• **Servidor:** {API_BASE}\n"
            f"• **Modelo Ativo:** {mdisp} (`{mid}`)\n"
            f"• **Modo de Raciocínio:** {cfg['nome']}\n"
            f"• **Ferramentas Ativas:** {'Sim' if FERRAMENTAS_HABILITADAS else 'Não (Modo Rápido)'}\n"
            f"• **Módulos MCP Ativos:** {', '.join(modulos)}\n"
            f"• **Total de Ferramentas Habilitadas:** {len(ferramentas_atuais)}\n"
            f"• **Mensagens no Histórico:** {len(historico)}",
            title="[bold cyan]Status do Agente[/bold cyan]",
            border_style="cyan"
        ))
        return True
        
    elif cmd_base in ("/ajuda", "/help", "/?"):
        console.print(Panel(
            "**🧠 Modos de Raciocínio & Atalhos:**\n"
            "• Pressione **[bold yellow]Shift + Tab[/bold yellow]** ou **[bold yellow]F2[/bold yellow]** para alternar modos em tempo real!\n"
            "• `/modo normal`       ➔ Modo ⚡ Rápido e Direto (Min-P 0.05)\n"
            "• `/modo think`        ➔ Modo 🧠 Pensamento Profundo (Chain of Thought)\n"
            "• `/modo reflexao`     ➔ Modo 🛡️ Auto-Reflexão e Auditoria Interna\n"
            "• `/tools on/off`      ➔ Liga ou desliga ferramentas no disco (para acelerar o GLM)\n\n"
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
    
    if not testar_servidor():
        console.print(Panel(
            "[bold red][X] Servidor de IA não encontrado em http://127.0.0.1:8080[/bold red]\n\n"
            "Por favor, inicie o servidor primeiro usando o atalho:\n"
            "[yellow]1 - Iniciar Servidor de IA (Qwen ou GLM).lnk[/yellow]",
            border_style="red"
        ))
        input("\nPressione ENTER para fechar...")
        return
        
    mid, mdisp = obter_modelo_ativo()
    is_glm = "glm" in mid.lower()
    
    console.print(Panel.fit(
        f"[bold cyan]🤖 Agente Nativo Universal ({mdisp})[/bold cyan]\n"
        f"[dim]Dual GPU • 3 Modos de Reasoning (Shift+Tab) • Skills de Elite • MCP Dinâmico[/dim]\n\n"
        f"• Conectado ao modelo: [bold green]{mdisp}[/bold green] (ID: `{mid}`)\n"
        f"• Pressione [bold yellow]Shift + Tab[/bold yellow] ou [bold yellow]F2[/bold yellow] para alternar: [green]⚡ NORMAL[/green] | [cyan]🧠 PENSAMENTO[/cyan] | [magenta]🛡️ REFLEXÃO[/magenta]\n"
        f"• Digite [cyan]/ajuda[/cyan] para ver todas as Skills e comandos\n"
        f"• Digite [bold red]sair[/bold red] para encerrar.",
        border_style="cyan"
    ))
    
    historico = [
        {"role": "system", "content": gerar_prompt_sistema(mdisp, is_glm)}
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
                title=f"[bold cyan]{mdisp} ({cfg['nome']})[/bold cyan]",
                border_style="cyan",
                padding=(1, 2)
            ))
            console.print()
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Encerrando agente...[/yellow]")
            break

if __name__ == "__main__":
    main()
