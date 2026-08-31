"""
Ferramentas Nativas do Agente Qwen 27B
Implementações diretas de alta performance para o sistema operacional.
"""

import os
import subprocess
import fnmatch
from pathlib import Path
from typing import Dict, Any, List, Optional

def ler_arquivo(caminho: str, linha_inicio: Optional[int] = None, linha_fim: Optional[int] = None) -> str:
    """Lê o conteúdo de um arquivo de texto com suporte a encoding automático e paginação de linhas."""
    p = Path(caminho).resolve()
    if not p.exists():
        return f"Erro: O arquivo '{caminho}' não existe."
    if not p.is_file():
        return f"Erro: '{caminho}' é um diretório, não um arquivo."
        
    conteudo = None
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            with open(p, "r", encoding=enc) as f:
                linhas = f.readlines()
            conteudo = linhas
            break
        except UnicodeDecodeError:
            continue
            
    if conteudo is None:
        return f"Erro: Não foi possível decodificar o arquivo '{caminho}'."
        
    total_linhas = len(conteudo)
    start = max(1, linha_inicio) if linha_inicio else 1
    end = min(total_linhas, linha_fim) if linha_fim else total_linhas
    
    linhas_selecionadas = conteudo[start - 1 : end]
    resultado = [f"--- Arquivo: {p} (Linhas {start}-{end} de {total_linhas}) ---"]
    for i, linha in enumerate(linhas_selecionadas, start=start):
        resultado.append(f"{i:4d} | {linha.rstrip()}")
        
    return "\n".join(resultado)

def listar_pasta(caminho: str = ".", profundidade: int = 1, apenas_pastas: bool = False) -> str:
    """Lista o conteúdo estruturado de uma pasta no disco."""
    p = Path(caminho).resolve()
    if not p.exists():
        return f"Erro: A pasta '{caminho}' não existe."
    if not p.is_dir():
        return f"Erro: '{caminho}' é um arquivo, não uma pasta."
        
    linhas = [f"Diretório: {p}"]
    
    def _listar(dir_path: Path, current_depth: int, prefix: str = ""):
        if current_depth > profundidade:
            return
        try:
            itens = sorted(list(dir_path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            linhas.append(f"{prefix}[Acesso Negado]")
            return
            
        for i, item in enumerate(itens):
            is_last = (i == len(itens) - 1)
            char = "└── " if is_last else "├── "
            sub_prefix = "    " if is_last else "│   "
            
            if item.is_dir():
                linhas.append(f"{prefix}{char}📁 {item.name}/")
                if current_depth < profundidade:
                    _listar(item, current_depth + 1, prefix + sub_prefix)
            elif not apenas_pastas:
                size_kb = item.stat().st_size / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
                linhas.append(f"{prefix}{char}📄 {item.name} ({size_str})")
                
    _listar(p, 1)
    return "\n".join(linhas)

def buscar_texto(termo: str, caminho: str = ".", extensao: Optional[str] = None) -> str:
    """Busca por um termo de texto dentro dos arquivos de um diretório recursivamente."""
    p = Path(caminho).resolve()
    if not p.exists():
        return f"Erro: O caminho '{caminho}' não existe."
        
    matches = []
    ignorar_pastas = {".git", "node_modules", ".venv", "__pycache__", "dist", "build"}
    
    for root, dirs, files in os.walk(p):
        dirs[:] = [d for d in dirs if d not in ignorar_pastas]
        for file in files:
            if extensao and not file.endswith(extensao):
                continue
            fpath = Path(root) / file
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, 1):
                        if termo.lower() in line.lower():
                            matches.append(f"{fpath.relative_to(p)}:{line_no}: {line.strip()[:150]}")
                            if len(matches) >= 50:
                                break
            except Exception:
                continue
        if len(matches) >= 50:
            break
            
    if not matches:
        return f"Nenhuma ocorrência de '{termo}' encontrada em '{caminho}'."
    return f"Resultados para '{termo}' ({len(matches)} correspondências):\n" + "\n".join(matches)

def escrever_arquivo(caminho: str, conteudo: str) -> str:
    """Cria ou sobrescreve um arquivo de texto com o conteúdo especificado."""
    p = Path(caminho).resolve()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(conteudo)
        return f"Arquivo gravado com sucesso: {p} ({len(conteudo)} caracteres)"
    except Exception as e:
        return f"Erro ao gravar arquivo: {str(e)}"

def editar_arquivo(caminho: str, texto_antigo: str, texto_novo: str) -> str:
    """Substitui um trecho específico de texto dentro de um arquivo existente."""
    p = Path(caminho).resolve()
    if not p.exists():
        return f"Erro: O arquivo '{caminho}' não existe."
        
    try:
        with open(p, "r", encoding="utf-8") as f:
            original = f.read()
            
        if texto_antigo not in original:
            return f"Erro: O trecho especificado em 'texto_antigo' não foi encontrado exatamente no arquivo."
            
        modificado = original.replace(texto_antigo, texto_novo, 1)
        with open(p, "w", encoding="utf-8") as f:
            f.write(modificado)
        return f"Arquivo '{p.name}' editado com sucesso."
    except Exception as e:
        return f"Erro ao editar arquivo: {str(e)}"

def executar_comando(comando: str, pasta: str = ".") -> str:
    """Executa um comando no shell do sistema (PowerShell/CMD) e retorna a saída."""
    p = Path(pasta).resolve()
    if not p.exists():
        return f"Erro: A pasta '{pasta}' não existe."
        
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", comando],
            cwd=str(p),
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace"
        )
        stdout = res.stdout.strip()
        stderr = res.stderr.strip()
        
        saida = []
        if stdout:
            saida.append(stdout)
        if stderr:
            saida.append(f"[STDERR]:\n{stderr}")
        if not stdout and not stderr:
            saida.append(f"[Comando executado com código de saída {res.returncode}]")
        return "\n".join(saida)
    except subprocess.TimeoutExpired:
        return "Erro: O comando excedeu o tempo limite de 120 segundos."
    except Exception as e:
        return f"Erro ao executar comando: {str(e)}"

# Mapeamento de esquemas JSON para o llama-server / OpenAI API
ESQUEMA_FERRAMENTAS = [
    {
        "type": "function",
        "function": {
            "name": "ler_arquivo",
            "description": "Lê o conteúdo de um arquivo de texto no disco. Pode ler o arquivo inteiro ou um intervalo de linhas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "caminho": {
                        "type": "string",
                        "description": "Caminho absoluto ou relativo do arquivo a ser lido."
                    },
                    "linha_inicio": {
                        "type": "integer",
                        "description": "Linha inicial a ser lida (opcional, 1-indexado)."
                    },
                    "linha_fim": {
                        "type": "integer",
                        "description": "Linha final a ser lida (opcional, inclusive)."
                    }
                },
                "required": ["caminho"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "listar_pasta",
            "description": "Lista os arquivos e subdiretórios de uma pasta no disco em formato de árvore.",
            "parameters": {
                "type": "object",
                "properties": {
                    "caminho": {
                        "type": "string",
                        "description": "Caminho da pasta a ser listada (padrão é '.')."
                    },
                    "profundidade": {
                        "type": "integer",
                        "description": "Nível de profundidade de subpastas a listar (padrão: 1)."
                    }
                },
                "required": ["caminho"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_texto",
            "description": "Busca por uma palavra, frase ou símbolo de código em múltiplos arquivos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "termo": {
                        "type": "string",
                        "description": "Texto ou símbolo a ser pesquisado."
                    },
                    "caminho": {
                        "type": "string",
                        "description": "Diretório onde iniciar a busca (padrão '.')."
                    },
                    "extensao": {
                        "type": "string",
                        "description": "Filtrar por extensão de arquivo (ex: '.py', '.js', '.md')."
                    }
                },
                "required": ["termo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escrever_arquivo",
            "description": "Cria um novo arquivo ou substitui completamente o conteúdo de um arquivo existente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "caminho": {
                        "type": "string",
                        "description": "Caminho do arquivo a ser criado ou substituído."
                    },
                    "conteudo": {
                        "type": "string",
                        "description": "O conteúdo de texto completo a ser gravado no arquivo."
                    }
                },
                "required": ["caminho", "conteudo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "editar_arquivo",
            "description": "Substitui um bloco específico de texto dentro de um arquivo existente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "caminho": {
                        "type": "string",
                        "description": "Caminho do arquivo a modificar."
                    },
                    "texto_antigo": {
                        "type": "string",
                        "description": "O texto exato existente a ser substituído."
                    },
                    "texto_novo": {
                        "type": "string",
                        "description": "O novo texto que substituirá o texto antigo."
                    }
                },
                "required": ["caminho", "texto_antigo", "texto_novo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "executar_comando",
            "description": "Executa um comando no PowerShell/Terminal do Windows e retorna a saída.",
            "parameters": {
                "type": "object",
                "properties": {
                    "comando": {
                        "type": "string",
                        "description": "O comando a ser executado (ex: 'npm test', 'git status', 'python main.py')."
                    },
                    "pasta": {
                        "type": "string",
                        "description": "Pasta de trabalho onde executar o comando (padrão '.')."
                    }
                },
                "required": ["comando"]
            }
        }
    }
]

MAPA_FUNCOES = {
    "ler_arquivo": ler_arquivo,
    "listar_pasta": listar_pasta,
    "buscar_texto": buscar_texto,
    "escrever_arquivo": escrever_arquivo,
    "editar_arquivo": editar_arquivo,
    "executar_comando": executar_comando
}

def despachar_ferramenta(nome: str, argumentos: Dict[str, Any]) -> str:
    """Executa a ferramenta solicitada e retorna o resultado formatado."""
    func = MAPA_FUNCOES.get(nome)
    if not func:
        return f"Erro: Ferramenta '{nome}' não reconhecida."
    try:
        return str(func(**argumentos))
    except Exception as e:
        return f"Erro ao executar '{nome}': {str(e)}"
