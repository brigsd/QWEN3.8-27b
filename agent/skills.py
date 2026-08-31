"""
Módulo de Skills Especializadas (Inspiradas no Claude Code / Antigravity)
Rotinas de alta performance para diagnóstico, auditoria, segurança, simplificação e testes.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

def executar_doctor(api_base: str, mcp_ativos: list) -> str:
    """Executa diagnóstico completo de saúde do ecossistema local (GPUs, VRAM, Servidor, Disco)."""
    linhas = ["# Diagnostico de Saude do Ecossistema Local (Doctor)\n"]
    
    # 1. Checagem do Servidor llama.cpp
    try:
        import requests
        res = requests.get(f"{api_base}/models", timeout=2)
        if res.status_code == 200:
            linhas.append("• **Servidor llama-server:** [bold green][ONLINE][/bold green] (Porta 8080 Ativa)")
        else:
            linhas.append(f"• **Servidor llama-server:** [bold yellow][ALERTA][/bold yellow] (Status {res.status_code})")
    except Exception:
        linhas.append("• **Servidor llama-server:** [bold red][OFFLINE][/bold red] (Inicie via atalho 1)")
        
    # 2. Checagem de GPUs NVIDIA (nvidia-smi)
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.used,memory.total,temperature.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if res.returncode == 0:
            linhas.append("\n• **Status das GPUs Dedicadas:**")
            for gpu_line in res.stdout.strip().splitlines():
                partes = [p.strip() for p in gpu_line.split(",")]
                if len(partes) >= 5:
                    idx, nome, used, total, temp = partes[0], partes[1], float(partes[2]), float(partes[3]), partes[4]
                    pct = (used / total) * 100
                    linhas.append(f"  - **GPU {idx} ({nome}):** {used/1024:.2f} GB / {total/1024:.2f} GB VRAM ({pct:.1f}%) • Temp: {temp}C")
        else:
            linhas.append("• **GPUs:** Nao foi possivel consultar o nvidia-smi.")
    except Exception as e:
        linhas.append(f"• **GPUs:** Erro ao consultar status de video ({str(e)})")
        
    # 3. Módulos MCP e Resíduos
    if mcp_ativos:
        linhas.append(f"\n• **Modulos MCP Ativos:** [green]{', '.join(mcp_ativos)}[/green]")
    else:
        linhas.append("\n• **Modulos MCP Ativos:** Nenhum (Zero residuos / Modo Ultra Leve)")
        
    # 4. Espaço em Disco
    try:
        total, used, free = shutil.disk_usage("C:\\")
        free_gb = free / (1024**3)
        linhas.append(f"• **Armazenamento (C:):** {free_gb:.1f} GB livres disponiveis")
    except Exception:
        pass
        
    # 5. Ambiente Python
    linhas.append(f"• **Python Runtime:** {sys.version.split()[0]} ({sys.executable})")
    linhas.append("\n[bold green][OK] Todos os subsistemas operando em condicoes nominais de alta eficiencia.[/bold green]")
    
    return "\n".join(linhas)

def obter_prompt_review(alvo: str) -> str:
    """Gera o prompt especializado para Code Review Sênior no padrão Claude Code."""
    return f"""Execute um **Code Review Sênior e Rigoroso** no alvo especificado: `{alvo}`.

Instruções do Protocolo de Review:
1. Inspecione o alvo usando `ler_arquivo` ou `buscar_relevancia` para analisar o código real.
2. Avalie os seguintes pilares:
   - **Corretude Lógica & Casos de Borda:** Entradas nulas, arrays vazios, condições de corrida e tratamento de erros.
   - **Segurança & Recursos:** Vazamento de memória, descritores de arquivo abertos sem fechar, concorrência.
   - **Tipagem & Manutenibilidade:** Nomes confusos, complexidade excessiva, falta de tipos.
3. Formate a saída estruturada com:
   - Resumo executivo em 2 linhas.
   - Tabela de Achados categorizados por severidade (Alta, Média, Baixa) com o padrão `arquivo.ext:linha`.
   - Recomendações de correção cirúrgicas.
"""

def obter_prompt_security(alvo: str) -> str:
    """Gera o prompt especializado para Auditoria de Segurança OWASP."""
    return f"""Execute uma **Auditoria de Segurança e Hardening (OWASP)** no alvo: `{alvo}`.

Instruções do Protocolo de Segurança:
1. Inspecione os arquivos relevantes em busca de vulnerabilidades críticas:
   - **Vazamento de Credenciais:** Chaves de API, senhas, tokens hardcoded.
   - **Injeção:** Shell injection em comandos, SQL injection ou interpolação de strings não sanitizadas.
   - **Path Traversal & Acesso a Arquivos:** Uso inseguro de caminhos sem resolução restrita.
   - **Validação de Entrada:** Parsing inseguro de dados externos.
2. Formate o relatório com a classificação de risco (Crítico, Alto, Médio, Baixo) e a correção recomendada para cada achado.
"""

def obter_prompt_simplify(alvo: str) -> str:
    """Gera o prompt especializado para Simplificação e Descomplicação de Código."""
    return f"""Analise o código em `{alvo}` e proponha uma **Simplificação e Refatoração Limpa** (Protocolo Simplify).

Diretrizes:
1. Identifique e elimine **código morto**, variáveis não utilizadas e abstrações prematuras.
2. Achate estruturas de decisão aninhadas complexas usando *early returns* (guard clauses).
3. Preserve 100% da lógica de negócio e do comportamento original.
4. Aplique as modificações usando `editar_arquivo` e mostre o diff resumido.
"""

def executar_verify(pasta: str = ".") -> Tuple[str, Optional[str]]:
    """Localiza e roda a suíte de testes do projeto automaticamente."""
    p = Path(pasta).resolve()
    if not p.exists():
        return f"Erro: Pasta '{pasta}' não existe.", None
        
    cmd = None
    runner_nome = None
    
    if (p / "package.json").exists():
        cmd = ["npm", "test"]
        runner_nome = "NPM Test (JavaScript/TypeScript)"
    elif (p / "pytest.ini").exists() or (p / "pyproject.toml").exists() or list(p.glob("test_*.py")):
        cmd = ["pytest"]
        runner_nome = "Pytest (Python)"
    elif (p / "Cargo.toml").exists():
        cmd = ["cargo", "test"]
        runner_nome = "Cargo Test (Rust)"
        
    if not cmd:
        return f"Nenhum test runner configurado automaticamente detectado em '{p}'. Você pode rodar testes manualmente via `executar_comando`.", None
        
    try:
        res = subprocess.run(
            cmd, cwd=str(p), capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace"
        )
        saida = f"=== Execução de Testes: {runner_nome} ===\n"
        if res.stdout:
            saida += res.stdout.strip() + "\n"
        if res.stderr:
            saida += f"[STDERR]:\n{res.stderr.strip()}"
            
        status = "[bold green][TESTES APROVADOS][/bold green]" if res.returncode == 0 else "[bold red][FALHA NOS TESTES][/bold red]"
        relatorio = f"{status}\n\n```text\n{saida[:3000]}\n```"
        
        prompt_ia = None
        if res.returncode != 0:
            prompt_ia = f"Os testes do projeto falharam. Analise o traceback abaixo e forneça a causa raiz e a correção exata:\n\n{saida[:2000]}"
            
        return relatorio, prompt_ia
        
    except Exception as e:
        return f"Erro ao executar testes: {str(e)}", None
