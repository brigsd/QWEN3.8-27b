# 🚀 Qwen 3.8 27B Local: Dual GPU, Agente Nativo, BM25 e MCP Dinâmico

Ambiente de execução local de alta performance para o modelo **Qwen 3.8 27B**, com aceleração por **Dual GPU (RTX 5070 + RTX 2080 Ti = 23.4 GB VRAM)**, suporte a contextos gigantes de **64k (8-bit) e 128k (4-bit)**, motor de recuperação **BM25 em Python puro** e arquitetura de **Agente Nativo com controle dinâmico de MCP (`/mcp`) sem resíduos de contexto**.

---

## 📑 Índice
1. [⚡ Quickstart (Início Rápido)](#-quickstart-início-rápido-em-3-passos)
2. [🤖 Módulo do Agente Nativo com Tool Calling](#-módulo-do-agente-nativo-com-tool-calling)
3. [🔌 Sistema de MCP Dinâmico (`/mcp` - Zero Ghost Tools)](#-sistema-de-mcp-dinâmico-mcp---zero-ghost-tools)
4. [🔍 Motor de Busca BM25 Offline (Inspirado no Moonwalk)](#-motor-de-busca-bm25-offline)
5. [🧠 Esquema da Janela de Contexto (64k vs 128k)](#-esquema-da-janela-de-contexto)
6. [🖥️ Lançadores e Atalhos Disponíveis](#️-lançadores-e-atalhos-disponíveis)
7. [⚙️ Hardware de Referência](#️-hardware-de-referência)

---

## ⚡ Quickstart (Início Rápido em 3 Passos)

Clone o repositório e execute os scripts de configuração automatizados no PowerShell:

```powershell
# 1. Instalar as dependências leves (Rich + Requests + Hugging Face CLI)
pip install -r requirements.txt

# 2. Baixar os binários otimizados do llama.cpp (com suporte a CUDA 13)
powershell -ExecutionPolicy Bypass -File .\setup\setup_server.ps1

# 3. Baixar o modelo Qwen 3.8 27B quantizado (17.8 GB)
powershell -ExecutionPolicy Bypass -File .\setup\download_model.ps1

# (Opcional) Gerar os atalhos com 1 clique na Área de Trabalho
powershell -ExecutionPolicy Bypass -File .\setup\create_shortcuts.ps1
```

---

## 🤖 Módulo do Agente Nativo com Tool Calling

O projeto conta com um **Agente Autônomo próprio (`agent/`)** que se comunica diretamente com a API do `llama-server` via **OpenAI Function Calling Nativo**:

```
       [ Você no Terminal ]
               │
               ▼  "o que faz o motor de prancha no mecanifica?"
      ┌─────────────────┐
      │  Qwen 3.8 27B   │
      │  (llama-server) │
      └────────┬────────┘
               │ ⚡ Emite Tool Call: buscar_relevancia(query="motor de prancha")
               ▼
    ┌──────────────────────┐
    │  Ferramentas Nativas │ ──► Indexa e busca no projeto em 800ms
    │     (agent/tools.py) │ ◄── Retorna apenas o trecho cirúrgico (~150 tokens)
    └──────────┬───────────┘
               │
               ▼ Conteúdo direto na memória de atenção
      ┌─────────────────┐
      │  Qwen 3.8 27B   │ ──► Resposta técnica exata em português perfeito.
      └─────────────────┘
```

### 🧰 Ferramentas Nativas Base (Sempre Ativas):
* 🔍 **`buscar_relevancia(query, caminho, top_n)`**: Motor BM25 offline para recuperação semântica em múltiplos arquivos.
* 📄 **`ler_arquivo(caminho, linha_inicio, linha_fim)`**: Leitura com paginação e detecção automática de encoding (UTF-8, Latin-1, CP1252).
* 📁 **`listar_pasta(caminho, profundidade)`**: Listagem hierárquica em árvore com tamanho de arquivos.
* 🔎 **`buscar_texto(termo, caminho, extensao)`**: Busca rápida recursiva estilo Grep/Ripgrep.
* ✏️ **`escrever_arquivo(caminho, conteudo)`**: Criação e gravação segura de arquivos.
* 🔧 **`editar_arquivo(caminho, texto_antigo, texto_novo)`**: Substituição cirúrgica de blocos de texto.
* 💻 **`executar_comando(comando, pasta)`**: Execução de scripts no PowerShell com captura de stdout/stderr.

---

## 🔌 Sistema de MCP Dinâmico (`/mcp` - Zero Ghost Tools)

Para evitar sobrecarga de contexto e impedir que o modelo sofra com **ferramentas fantasmas** (*ghost tools*), o agente implementa **injeção e ejeção dinâmica de ferramentas em tempo de execução**:

```
                       [ Você no Chat ]
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
       `/mcp on mecanifica`              `/mcp off`
               │                             │
    ⚡ Injeta ferramentas 3D       🧹 Remove 100% dos esquemas JSON
    no payload do Qwen (10 tools)  do payload da API (volta para 7)
               │                             │
               ▼                             ▼
   O modelo passa a saber         O modelo LITERALMENTE não tem
   exportar STEP, OBJ e peças.    como chamar ou alucinar essas tools!
```

### 🎮 Comandos de Barra Disponíveis no Chat:

| Comando | Função |
| :--- | :--- |
| **`/mcp list`** | Lista os módulos MCP disponíveis e o status atual (🟢 ATIVO / ⚪ DESATIVADO). |
| **`/mcp on mecanifica`** | Ativa ferramentas 3D CAD (`exportar_step`, `exportar_obj`, `descrever_peca`). |
| **`/mcp on web`** | Ativa busca em tempo real no DuckDuckGo e leitura de páginas web (`buscar_web`, `ler_pagina_web`). |
| **`/mcp on all`** | Ativa todos os módulos MCP de uma só vez. |
| **`/mcp off [nome]`** | Desliga um módulo específico ou **todos os módulos (`/mcp off`)**, zerando resíduos. |
| **`/status`** | Exibe o total de ferramentas ativas na atenção do Qwen e contagem de histórico. |
| **`/limpar`** | Reseta a memória da sessão atual. |
| **`/ajuda`** | Exibe o menu de comandos rápidos. |

---

## 🔍 Motor de Busca BM25 Offline

Inspirado no projeto **Moonwalk AutoDraft**, o motor `agent/retriever.py` implementa o algoritmo de ranqueamento probabilístico **BM25 (Best Matching 25)** em **100% Python puro**, sem necessidade de bancos vetoriais pesados:

* **Velocidade de Indexação:** Varre e indexa repositórios com centenas de arquivos em **menos de 800 milissegundos**.
* **Economia de Contexto:** Reduz o consumo de tokens de investigações longas em **+99.9%** (injeta ~90-150 tokens em vez de milhares de linhas brutas).
* **Proteção de VRAM:** Mantém a janela de atenção do Qwen limpa para respostas mais rápidas e sem degradação.

---

## 🧠 Esquema da Janela de Contexto

Otimização de memória do **KV Cache** aliada ao **Flash Attention (`-fa on`)** e alocação de slot único (`-np 1`):

```
                          ┌───────────────────────────┐
                          │   Qwen 3.8 27B (17.8 GB)  │
                          └─────────────┬─────────────┘
                                        │
           ┌────────────────────────────┴────────────────────────────┐
           ▼                                                         ▼
┌───────────────────────────────────────┐ ┌───────────────────────────────────────┐
│       MODO PRECISÃO (64K TOKENS)      │ │        MODO GIGANTE (128K TOKENS)     │
├───────────────────────────────────────┤ ├───────────────────────────────────────┤
│ • Quantização: 8-bit (q8_0)           │ │ • Quantização: 4-bit (q4_0)           │
│ • Perda de Precisão: < 0.01% (Zero)   │ │ • Perda de Precisão: ~2% (Leve)       │
│ • Uso de VRAM: ~20.6 GB (Total)       │ │ • Uso de VRAM: ~22.6 GB (Total)       │
│ • Folga VRAM: ~2.8 GB livres          │ │ • Folga VRAM: ~0.8 GB livres          │
│ • Foco: Programação e Sintaxe Fina    │ │ • Foco: Web Chat, Livros, PDFs Longos │
└───────────────────────────────────────┘ └───────────────────────────────────────┘
```

| Parâmetro | Modo Precisão (64k) | Modo Gigante (128k) |
| :--- | :--- | :--- |
| **Comando de Ativação** | `-c 65536 -ctk q8_0 -ctv q8_0` | `-c 131072 -ctk q4_0 -ctv q4_0` |
| **Capacidade de Leitura** | ~50 páginas de código | ~100 páginas de texto/documentação |
| **Aceleração** | Flash Attention (`-fa on`) | Flash Attention (`-fa on`) |
| **Uso Total de VRAM** | **~20.6 GB** de 23.4 GB | **~22.6 GB** de 23.4 GB |

---

## 🖥️ Lançadores e Atalhos Disponíveis

| Script | Atalho na Área de Trabalho | Função |
| :--- | :--- | :--- |
| **`scripts/1-iniciar_servidor_llama.bat`** | `1 - Iniciar Servidor Qwen 27B.lnk` | Detecta GPUs e abre o menu de escolha (64k vs 128k). |
| **`scripts/1-iniciar_servidor_128k_gigante.bat`** | `1b - Iniciar Servidor Direto (128k Gigante).lnk` | Inicia o servidor diretamente no modo 128k 4-bit. |
| **`scripts/2-iniciar_aider_com_llama.bat`** | `2 - Abrir Claude Code Local (Aider).lnk` | Abre o Aider configurado com Diff em PT-BR. |
| **`scripts/3-iniciar_agente_nativo.bat`** | `3 - Abrir Agente Nativo (Qwen 27B).lnk` | Abre o **Agente Nativo** interativo com BM25 e `/mcp`. |

---

## ⚙️ Hardware de Referência

* **Placa-Mãe:** MSI MAG Z790 TOMAHAWK
* **GPU 0 (Display Principal):** NVIDIA GeForce RTX 5070 (12 GB GDDR7)
* **GPU 1 (Acelerador Secundário):** NVIDIA GeForce RTX 2080 Ti (11 GB GDDR6)
* **VRAM Combinada:** **23.4 GB**
* **Memória RAM:** 32 GB DDR5
* **Desempenho Médio:** ~35 a 40+ tokens/s com 100% de offload na VRAM.
