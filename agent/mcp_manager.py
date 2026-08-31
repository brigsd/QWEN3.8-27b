"""
Gerenciador Dinâmico de Ferramentas e Módulos MCP
Permite ativar/desativar pacotes de ferramentas sob demanda sem deixar resíduos no modelo.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple

# 1. Ferramentas Web
from web_tools import ESQUEMA_WEB, MAPA_WEB

# 2. Ferramentas do Mecanifica
MECANIFICA_ROOT = Path(r"C:\Users\micro\Desktop\mecanifica")

def mecanifica_descrever_peca(nome_peca: str = "", listar: bool = False) -> str:
    """Descreve os passos e geometria de uma peça do Mecanifica ou lista as disponíveis."""
    if not MECANIFICA_ROOT.exists():
        return f"Erro: Pasta do Mecanifica não encontrada em '{MECANIFICA_ROOT}'."
    cmd = ["node", "tools/mecanifica/descrever-peca.mjs"]
    if listar or not nome_peca:
        cmd.append("--listar")
    else:
        cmd.append(nome_peca)
    try:
        res = subprocess.run(cmd, cwd=str(MECANIFICA_ROOT), capture_output=True, text=True, encoding="utf-8", timeout=30)
        return res.stdout.strip() or res.stderr.strip()
    except Exception as e:
        return f"Erro ao executar descrever-peca: {str(e)}"

def mecanifica_exportar_obj(nome: str) -> str:
    """Exporta uma peça ou montagem procedural do Mecanifica para formato OBJ 3D."""
    if not MECANIFICA_ROOT.exists():
        return f"Erro: Pasta do Mecanifica não encontrada em '{MECANIFICA_ROOT}'."
    cmd = ["node", "tools/mecanifica/exportar-obj.mjs", nome]
    try:
        res = subprocess.run(cmd, cwd=str(MECANIFICA_ROOT), capture_output=True, text=True, encoding="utf-8", timeout=30)
        return res.stdout.strip() or res.stderr.strip()
    except Exception as e:
        return f"Erro ao exportar OBJ: {str(e)}"

def mecanifica_exportar_step(nome: str) -> str:
    """Exporta uma peça ou montagem procedural do Mecanifica para formato CAD STEP."""
    if not MECANIFICA_ROOT.exists():
        return f"Erro: Pasta do Mecanifica não encontrada em '{MECANIFICA_ROOT}'."
    cmd = ["node", "tools/mecanifica/exportar-step.mjs", nome]
    try:
        res = subprocess.run(cmd, cwd=str(MECANIFICA_ROOT), capture_output=True, text=True, encoding="utf-8", timeout=30)
        return res.stdout.strip() or res.stderr.strip()
    except Exception as e:
        return f"Erro ao exportar STEP: {str(e)}"

ESQUEMA_MECANIFICA = [
    {
        "type": "function",
        "function": {
            "name": "mecanifica_descrever_peca",
            "description": "Descreve os passos e geometria de uma peça procedural do projeto Mecanifica ou lista peças disponíveis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome_peca": {
                        "type": "string",
                        "description": "Nome da peça a descrever (deixe vazio se quiser apenas listar)."
                    },
                    "listar": {
                        "type": "boolean",
                        "description": "Se verdadeiro, lista todas as peças do catálogo."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mecanifica_exportar_obj",
            "description": "Exporta uma peça ou montagem procedural do Mecanifica para um arquivo de malha 3D (.OBJ).",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome da peça ou montagem procedural a exportar."
                    }
                },
                "required": ["nome"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mecanifica_exportar_step",
            "description": "Exporta uma peça ou montagem procedural do Mecanifica para formato CAD B-Rep (.STEP / STP).",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {
                        "type": "string",
                        "description": "Nome da peça ou montagem procedural a exportar."
                    }
                },
                "required": ["nome"]
            }
        }
    }
]

MAPA_MECANIFICA = {
    "mecanifica_descrever_peca": mecanifica_descrever_peca,
    "mecanifica_exportar_obj": mecanifica_exportar_obj,
    "mecanifica_exportar_step": mecanifica_exportar_step
}

# 3. Registro Central de Módulos MCP
MODULOS_DISPONIVEIS = {
    "web": {
        "descricao": "Pesquisa no DuckDuckGo e Leitura de Páginas Web em tempo real",
        "esquema": ESQUEMA_WEB,
        "funcoes": MAPA_WEB
    },
    "mecanifica": {
        "descricao": "Ferramentas 3D CAD e Procedurais do Projeto Mecanifica (STEP, OBJ, Peças)",
        "esquema": ESQUEMA_MECANIFICA,
        "funcoes": MAPA_MECANIFICA
    }
}

class MCPManager:
    """Gerencia ativação e desativação semântica de módulos MCP em tempo de execução."""
    def __init__(self):
        self.modulos_ativos = set()

    def ativar(self, nome: str) -> Tuple[bool, str]:
        nome = nome.lower().strip()
        if nome == "all" or nome == "todos":
            for k in MODULOS_DISPONIVEIS:
                self.modulos_ativos.add(k)
            return True, f"Todos os módulos MCP foram ativados: {', '.join(MODULOS_DISPONIVEIS.keys())}"
            
        if nome not in MODULOS_DISPONIVEIS:
            return False, f"Módulo MCP '{nome}' não encontrado. Disponíveis: {', '.join(MODULOS_DISPONIVEIS.keys())}"
            
        self.modulos_ativos.add(nome)
        return True, f"Módulo MCP '{nome}' ativado com sucesso ({MODULOS_DISPONIVEIS[nome]['descricao']})."

    def desativar(self, nome: str = "") -> Tuple[bool, str]:
        nome = nome.lower().strip()
        if not nome or nome in ("all", "todos"):
            qtde = len(self.modulos_ativos)
            self.modulos_ativos.clear()
            return True, f"Todos os módulos MCP foram desativados ({qtde} módulos desligados). O modelo agora opera apenas com ferramentas nativas essenciais."
            
        if nome in self.modulos_ativos:
            self.modulos_ativos.remove(nome)
            return True, f"Módulo MCP '{nome}' desativado com sucesso. As ferramentas dele foram removidas do modelo."
        else:
            return False, f"Módulo '{nome}' não estava ativo."

    def listar_status(self) -> str:
        linhas = ["📦 **Módulos MCP e Extensões Disponíveis:**\n"]
        for k, v in MODULOS_DISPONIVEIS.items():
            status = "🟢 [bold green]ATIVO[/bold green]" if k in self.modulos_ativos else "⚪ [dim]DESATIVADO[/dim]"
            total_tools = len(v["esquema"])
            linhas.append(f"• **{k}** ({status}): {v['descricao']} ({total_tools} ferramentas)")
            
        linhas.append("\nComandos:")
        linhas.append("  `/mcp on <nome>`  ➔ Ativa um módulo (ex: `/mcp on mecanifica` ou `/mcp on web`)")
        linhas.append("  `/mcp off [nome]` ➔ Desativa um módulo ou todos (`/mcp off`)")
        return "\n".join(linhas)

    def obter_ferramentas_ativas(self, ferramentas_base: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Retorna a lista combinada de schemas JSON contendo apenas as ferramentas atualmente ativas."""
        resultado = list(ferramentas_base)
        for mod in self.modulos_ativos:
            if mod in MODULOS_DISPONIVEIS:
                resultado.extend(MODULOS_DISPONIVEIS[mod]["esquema"])
        return resultado

    def despachar(self, nome_func: str, args: Dict[str, Any]) -> Tuple[bool, Any]:
        """Tenta despachar a ferramenta para os módulos ativos."""
        for mod in self.modulos_ativos:
            funcs = MODULOS_DISPONIVEIS[mod]["funcoes"]
            if nome_func in funcs:
                try:
                    return True, str(funcs[nome_func](**args))
                except Exception as e:
                    return True, f"Erro ao executar ferramenta MCP '{nome_func}': {str(e)}"
        return False, None
