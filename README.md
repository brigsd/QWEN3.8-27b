# 🚀 Qwen 3.8 27B Local: Guia Completo, Dual GPU e Agente Nativo com Tool Calling

Ambiente de execução local de alta performance para o modelo **Qwen 3.8 27B**, com aceleração por **Dual GPU (RTX 5070 + RTX 2080 Ti = 23.4 GB VRAM)**, suporte a contextos gigantes de **64k (8-bit) e 128k (4-bit)** e módulo exclusivo de **Agente Nativo com Tool Calling instantâneo**.

---

## 📑 Índice
1. [⚡ Quickstart (Início Rápido)](#-quickstart-início-rápido-em-3-passos)
2. [🤖 Módulo do Agente Nativo (Tool Calling)](#-módulo-do-agente-nativo-tool-calling)
3. [🧠 Esquema da Janela de Contexto (64k vs 128k)](#-esquema-da-janela-de-contexto)
4. [🛠️ Guia de Configuração Passo a Passo](#️-guia-de-configuração-passo-a-passo)
5. [🖥️ Scripts e Lançadores Disponíveis](#️-scripts-e-lançadores-disponíveis)
6. [🌐 Como Conectar ao Web Chat no Navegador](#-como-conectar-ao-web-chat-no-navegador)
7. [⚙️ Hardware de Referência](#️-hardware-de-referência)

---

## ⚡ Quickstart (Início Rápido em 3 Passos)

Se você acabou de clonar este repositório, basta seguir estes passos no PowerShell:

```powershell
# 1. Instalar as dependências leves (Rich + Requests + Hugging Face CLI)
pip install -r requirements.txt

# 2. Baixar os binários otimizados do llama.cpp (com suporte a CUDA 13)
powershell -ExecutionPolicy Bypass -File .\setup\setup_server.ps1

# 3. Baixar o modelo Qwen 3.8 27B (17.8 GB)
powershell -ExecutionPolicy Bypass -File .\setup\download_model.ps1

# (Opcional) Criar atalhos automáticos na Área de Trabalho
powershell -ExecutionPolicy Bypass -File .\setup\create_shortcuts.ps1
```

---

## 🤖 Módulo do Agente Nativo (Tool Calling)

O projeto inclui um **Agente Autônomo próprio (`agent/`)** que se conecta diretamente à API do `llama-server` utilizando **Tool Calling Nativo**.

Diferente de frameworks antigos que geram e executam scripts temporários para cada ação, o nosso Agente Nativo despacha funções do sistema operacional em **menos de 1 milissegundo**:

```
       [ Você no Terminal ]
               │
               ▼  "leia o README da pasta C:\Projetos\App"
      ┌─────────────────┐
      │  Qwen 3.8 27B   │
      │  (llama-server) │
      └────────┬────────┘
               │ ⚡ Emite Tool Call: ler_arquivo(caminho="C:\...\README.md")
               ▼
    ┌──────────────────────┐
    │  Ferramentas Nativas │ ──► Lê o arquivo no disco em 0.5ms (UTF-8)
    │     (agent/tools.py) │ ◄── Retorna o conteúdo diretamente
    └──────────┬───────────┘
               │
               ▼ O conteúdo entra direto no contexto da IA
      ┌─────────────────┐
      │  Qwen 3.8 27B   │ ──► Resposta formatada em Markdown com resumo perfeito.
      └─────────────────┘
```

### 🧰 Ferramentas Nativas Inclusas:
* 📄 **`ler_arquivo(caminho, linha_inicio, linha_fim)`**: Leitura com detecção de encoding (UTF-8, Latin-1) e paginação.
* 📁 **`listar_pasta(caminho, profundidade)`**: Listagem estruturada em árvore com tamanho de arquivos.
* 🔍 **`buscar_texto(termo, caminho, extensao)`**: Busca recursiva estilo ripgrep em múltiplos arquivos.
* ✏️ **`escrever_arquivo(caminho, conteudo)`**: Criação e gravação atômica de arquivos.
* 🔧 **`editar_arquivo(caminho, texto_antigo, texto_novo)`**: Substituição precisa de blocos de texto.
* 💻 **`executar_comando(comando, pasta)`**: Execução de scripts no PowerShell com captura de stdout/stderr.

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

## 🖥️ Scripts e Lançadores Disponíveis

| Script | Atalho na Área de Trabalho | Função |
| :--- | :--- | :--- |
| **`scripts/1-iniciar_servidor_llama.bat`** | `1 - Iniciar Servidor Qwen 27B.lnk` | Detecta GPUs ativas e abre menu interativo (64k vs 128k). |
| **`scripts/1-iniciar_servidor_128k_gigante.bat`** | `1b - Iniciar Servidor Direto (128k Gigante).lnk` | Inicia o servidor diretamente no modo 128k 4-bit. |
| **`scripts/2-iniciar_aider_com_llama.bat`** | `2 - Abrir Claude Code Local (Aider).lnk` | Abre o Aider configurado com Diff em PT-BR. |
| **`scripts/3-iniciar_agente_nativo.bat`** | `3 - Abrir Agente Nativo (Qwen 27B).lnk` | Abre o **Agente Nativo** interativo com Tool Calling de alta performance. |

---

## 🌐 Como Conectar ao Web Chat no Navegador

Se você usa interfaces gráficas como **Open WebUI**, **LibreChat** ou extensões do navegador:

1. Inicie o servidor via `1-iniciar_servidor_llama.bat`.
2. Configure a conexão OpenAI API:
   * **URL Base:** `http://127.0.0.1:8080/v1`
   * **API Key:** `none`
   * **Model Name:** `qwen3.8-27b`

---

## ⚙️ Hardware de Referência

* **Placa-Mãe:** MSI MAG Z790 TOMAHAWK
* **GPU 0 (Display Principal):** NVIDIA GeForce RTX 5070 (12 GB GDDR7)
* **GPU 1 (Acelerador Secundário):** NVIDIA GeForce RTX 2080 Ti (11 GB GDDR6)
* **VRAM Combinada:** **23.4 GB**
* **Memória RAM:** 32 GB DDR5
* **Desempenho Médio:** ~35 a 40+ tokens/s com 100% de offload na VRAM.
