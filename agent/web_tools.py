"""
Ferramentas de Busca e Leitura Web para o Agente Local
Usa DuckDuckGo HTML e requests simples (sem necessidade de chaves de API pagas).
"""

import re
import urllib.parse
import requests
from typing import Dict, Any, List

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def buscar_web(query: str, max_resultados: int = 4) -> str:
    """Pesquisa na web via DuckDuckGo e retorna os principais resultados com título, URL e snippet."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return f"Erro ao acessar mecanismo de busca ({res.status_code})."

        html = res.text
        # Extrai links e snippets simples
        resultados = []
        blocos = html.split('<div class="result results_links results_links_deep web-result">')[1:]
        
        for bloco in blocos[:max_resultados]:
            # Titulo e Link
            match_link = re.search(r'<a class="result__url" href="([^"]+)".*?>(.*?)</a>', bloco, re.DOTALL)
            match_title = re.search(r'<a class="result__a"[^>]*>(.*?)</a>', bloco, re.DOTALL)
            match_snippet = re.search(r'<a class="result__snippet"[^>]*>(.*?)</a>', bloco, re.DOTALL)
            
            if match_title and match_snippet:
                titulo = re.sub(r'<[^>]+>', '', match_title.group(1)).strip()
                snippet = re.sub(r'<[^>]+>', '', match_snippet.group(1)).strip()
                link = match_link.group(1).strip() if match_link else ""
                
                # Desembrulha URL do DuckDuckGo se necessario
                if "uddg=" in link:
                    link = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])
                    
                resultados.append(f"🌐 **{titulo}**\nURL: {link}\n{snippet}\n")

        if not resultados:
            return f"Nenhum resultado web encontrado para '{query}'."
            
        return f"Resultados Web para '{query}':\n\n" + "\n".join(resultados)

    except Exception as e:
        return f"Erro na pesquisa web: {str(e)}"

def ler_pagina_web(url: str, max_caracteres: int = 3500) -> str:
    """Lê o conteúdo textual de uma URL e retorna o texto limpo em Markdown."""
    try:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            
        res = requests.get(url, headers=HEADERS, timeout=12)
        if res.status_code != 200:
            return f"Erro ao acessar {url} (Status {res.status_code})."
            
        html = res.text
        # Remove tags de script e style
        html = re.sub(r'<(script|style|nav|header|footer)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Extrai texto de tags basicas
        texto = re.sub(r'<[^>]+>', ' ', html)
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        if len(texto) > max_caracteres:
            texto = texto[:max_caracteres] + f"\n\n[... Truncado em {max_caracteres} caracteres. Use seletores se precisar de mais detalhes.]"
            
        return f"--- Conteúdo de {url} ---\n{texto}"
    except Exception as e:
        return f"Erro ao ler página web: {str(e)}"

ESQUEMA_WEB = [
    {
        "type": "function",
        "function": {
            "name": "buscar_web",
            "description": "Pesquisa na internet em tempo real (via DuckDuckGo) para consultar documentações atualizadas, bibliotecas, erros ou informações recentes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "O termo de pesquisa a buscar na internet."
                    },
                    "max_resultados": {
                        "type": "integer",
                        "description": "Número máximo de resultados a retornar (padrão: 4)."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ler_pagina_web",
            "description": "Lê o conteúdo de texto limpo de uma página da web a partir de sua URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "A URL completa da página a ser lida."
                    }
                },
                "required": ["url"]
            }
        }
    }
]

MAPA_WEB = {
    "buscar_web": buscar_web,
    "ler_pagina_web": ler_pagina_web
}
