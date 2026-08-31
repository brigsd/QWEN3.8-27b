"""
Motor de Busca por Relevância BM25 (Offline e Nativo)
Inspirado no algoritmo do Moonwalk AutoDraft para recuperação instantânea de contexto.
"""

import os
import math
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple, Optional

STOPWORDS = {
    # Portugues
    "a", "o", "e", "de", "da", "do", "das", "dos", "em", "no", "na", "nos",
    "nas", "um", "uma", "uns", "umas", "para", "por", "com", "sem", "sobre",
    "entre", "que", "se", "ao", "aos", "as", "os", "ser", "ter", "foi",
    "sao", "são", "como", "mais", "menos", "muito", "ja", "já", "nao", "não",
    "sim", "seu", "sua", "seus", "suas", "isso", "esse", "essa", "isto",
    "este", "esta", "ele", "ela", "eles", "elas", "eu", "me", "ou", "mas",
    "tambem", "também", "ate", "até", "quando", "onde", "qual", "quais",
    "quem", "porque", "pois", "entao", "então", "assim", "depois", "antes",
    "durante", "contra", "desde", "pelo", "pela", "qual", "como",
    # Ingles
    "the", "an", "and", "or", "but", "if", "then", "else", "when", "where",
    "which", "who", "this", "that", "these", "those", "i", "you", "he",
    "she", "it", "we", "they", "to", "of", "in", "on", "at", "by", "for",
    "with", "without", "from", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "not", "no", "yes", "so",
    "than", "too", "very", "can", "could", "should", "would", "will",
}

def tokenizar(texto: str) -> List[str]:
    """Divide o texto em tokens informativos removendo pontuações e stopwords."""
    if not texto:
        return []
    texto = texto.lower()
    texto = re.sub(r'[\#\*\_\[\]\(\)\-\`\>\:\n\r\t\\\/\{\}\;\,\.]', ' ', texto)
    tokens = re.findall(r'\b\w+\b', texto)
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]

class BM25Retriever:
    """Motor BM25 em memória para ranqueamento de relevância instantâneo."""
    def __init__(self, documentos: Dict[str, str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.N = len(documentos)
        self.raw_docs = documentos
        
        self.corpus = {}
        self.doc_lengths = {}
        self.doc_frequencies = Counter()
        
        for doc_id, texto in documentos.items():
            tokens = tokenizar(texto)
            self.corpus[doc_id] = tokens
            self.doc_lengths[doc_id] = len(tokens)
            for termo in set(tokens):
                self.doc_frequencies[termo] += 1
                
        self.avgdl = sum(self.doc_lengths.values()) / self.N if self.N > 0 else 0
        
        self.idf = {}
        for termo, freq in self.doc_frequencies.items():
            self.idf[termo] = math.log((self.N - freq + 0.5) / (freq + 0.5) + 1.0)

    def calcular_score(self, query_tokens: List[str], doc_id: str) -> Tuple[float, int]:
        tokens_doc = self.corpus[doc_id]
        contagem_doc = Counter(tokens_doc)
        doc_len = self.doc_lengths[doc_id]

        score = 0.0
        termos_casados = set()
        for termo in query_tokens:
            if termo not in self.idf:
                continue

            f_qi = contagem_doc[termo]
            if f_qi > 0:
                termos_casados.add(termo)
            idf_qi = self.idf[termo]

            numerador = f_qi * (self.k1 + 1.0)
            denominador = f_qi + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl)) if self.avgdl > 0 else 1.0

            score += idf_qi * (numerador / denominador)

        return score, len(termos_casados)

    def buscar(self, query_texto: str, top_n: int = 3, min_termos: int = 1) -> List[Tuple[str, float, str]]:
        """Retorna lista de (doc_id, score, trecho_relevante)."""
        query_tokens = tokenizar(query_texto)
        if not query_tokens or self.N == 0:
            return []

        exigidos = min(min_termos, len(set(query_tokens)))
        scores = []
        for doc_id in self.corpus:
            score, casados = self.calcular_score(query_tokens, doc_id)
            if score > 0 and casados >= exigidos:
                scores.append((doc_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        top_docs = scores[:top_n]
        
        resultados = []
        for doc_id, score in top_docs:
            trecho = self._extrair_melhor_trecho(self.raw_docs[doc_id], query_tokens)
            resultados.append((doc_id, score, trecho))
            
        return resultados

    def _extrair_melhor_trecho(self, texto: str, query_tokens: List[str], max_chars: int = 400) -> str:
        """Encontra o parágrafo ou trecho mais relevante dentro do documento."""
        paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
        if not paragrafos:
            return texto[:max_chars] + "..." if len(texto) > max_chars else texto
            
        melhor_p = paragrafos[0]
        max_casamentos = -1
        
        for p in paragrafos:
            p_tokens = set(tokenizar(p))
            casamentos = sum(1 for t in query_tokens if t in p_tokens)
            if casamentos > max_casamentos:
                max_casamentos = casamentos
                melhor_p = p
                
        if len(melhor_p) > max_chars:
            return melhor_p[:max_chars] + "..."
        return melhor_p

# Cache simples em memória para não reindexar o disco sem necessidade
_CACHE_RETRIEVER: Dict[str, Tuple[float, BM25Retriever]] = {}

def indexar_e_buscar(query: str, caminho_pasta: str = ".", top_n: int = 3, extensoes: Optional[List[str]] = None) -> str:
    """Carrega os arquivos da pasta, cria o índice BM25 e retorna os mais relevantes."""
    p = Path(caminho_pasta).resolve()
    if not p.exists() or not p.is_dir():
        return f"Erro: Pasta '{caminho_pasta}' não encontrada."

    exts = extensoes or [".md", ".py", ".js", ".ts", ".html", ".css", ".json", ".txt", ".bat", ".ps1"]
    ignorar = {".git", "node_modules", ".venv", "__pycache__", "dist", "build", "models", ".system_generated"}

    # Varre os arquivos
    documentos = {}
    total_docs = 0
    
    for root, dirs, files in os.walk(p):
        dirs[:] = [d for d in dirs if d not in ignorar]
        for f in files:
            fpath = Path(root) / f
            if any(f.endswith(ext) for ext in exts):
                try:
                    rel = str(fpath.relative_to(p)).replace("\\", "/")
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                        documentos[rel] = fp.read()
                    total_docs += 1
                except Exception:
                    continue

    if not documentos:
        return f"Nenhum arquivo compatível encontrado para indexação em '{caminho_pasta}'."

    retriever = BM25Retriever(documentos)
    resultados = retriever.buscar(query, top_n=top_n)

    if not resultados:
        return f"Nenhum documento com relevância significativa encontrado para '{query}' (Total indexado: {total_docs} arquivos)."

    saida = [f"Resultados BM25 para '{query}' ({len(resultados)} de {total_docs} arquivos analisados):"]
    for doc_id, score, trecho in resultados:
        saida.append(f"\n📄 **{doc_id}** (Score BM25: {score:.2f})")
        saida.append(f"```text\n{trecho}\n```")

    return "\n".join(saida)
