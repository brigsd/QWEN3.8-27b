# 🚀 Qwen 3.8 27B Local: Guia Completo de Configuração, Dual GPU e Agentes

Ambiente de execução local de alta performance para o modelo **Qwen 3.8 27B**, com aceleração por **Dual GPU (RTX 5070 + RTX 2080 Ti = 23.4 GB VRAM)**, suporte a contextos gigantes de **64k (8-bit) e 128k (4-bit)** e integração com agentes autônomos no terminal (**Open Interpreter** e **Aider**), além de conexão com interfaces Web (**Open WebUI**, **LibreChat**).

---

## 📑 Índice
1. [⚡ Quickstart (Início Rápido)](#-quickstart-início-rápido-em-3-passos)
2. [📋 Pré-requisitos](#-pré-requisitos)
3. [🛠️ Guia de Configuração Passo a Passo](#️-guia-de-configuração-passo-a-passo)
4. [🧠 Esquema da Janela de Contexto (64k vs 128k)](#-esquema-da-janela-de-contexto)
5. [🖥️ Scripts e Lançadores Disponíveis](#️-scripts-e-lançadores-disponíveis)
6. [🌐 Como Conectar ao Web Chat no Navegador](#-como-conectar-ao-web-chat-no-navegador)
7. [🤖 Como Usar os Agentes de Terminal](#-como-usar-os-agentes-de-terminal)
8. [⚙️ Hardware de Referência](#️-hardware-de-referência)

---

## ⚡ Quickstart (Início Rápido em 3 Passos)

Se você acabou de clonar este repositório, basta seguir estes passos no PowerShell:

```powershell
# 1. Instalar todas as dependências Python
pip install -r requirements.txt

# 2. Baixar os binários otimizados do llama.cpp (com suporte a CUDA 13)
powershell -ExecutionPolicy Bypass -File .\setup\setup_server.ps1

# 3. Baixar o modelo Qwen 3.8 27B (17.8 GB)
powershell -ExecutionPolicy Bypass -File .\setup\download_model.ps1

# (Opcional) Criar atalhos automáticos na Área de Trabalho
powershell -ExecutionPolicy Bypass -File .\setup\create_shortcuts.ps1
```

---

## 📋 Pré-requisitos

* **Sistema Operacional:** Windows 10 ou 11 (64-bit).
* **Python:** Versão 3.10, 3.11 ou 3.12 instalada e adicionada ao PATH do sistema.
* **Driver NVIDIA:** Driver Game Ready ou Studio atualizado (versão 560+ ou 600+) com suporte a CUDA 12/13.
* **Memória de Vídeo (VRAM):**
  * **Dual GPU (~22 a 24 GB VRAM):** Roda **100% das camadas na VRAM** em velocidade máxima (~35 a 40 tokens/s).
  * **GPU Única (12 GB VRAM):** O script detecta automaticamente e ativa o **Modo Híbrido** (aloca ~22 camadas na GPU e o restante na RAM DDR5).

---

## 🛠️ Guia de Configuração Passo a Passo

### Passo 1: Instalar as Dependências (`requirements.txt`)
O arquivo `requirements.txt` contém os pacotes necessários para o download do modelo e uso dos agentes:
```bash
pip install -r requirements.txt
```
* **`huggingface_hub[cli]`**: Permite baixar modelos diretamente do repositório Hugging Face com velocidade máxima e reconexão automática.
* **`aider-chat`**: O agente de código focado em repositórios Git (estilo Claude Code).
* **`open-interpreter`**: O agente com acesso total ao sistema operacional (executa scripts em PowerShell, CMD e manipula arquivos).

---

### Passo 2: Baixar os Binários do Servidor (`setup_server.ps1`)
Execute o script de configuração do servidor:
```powershell
powershell -ExecutionPolicy Bypass -File .\setup\setup_server.ps1
```
Esse script baixa a compilação oficial mais recente do **llama.cpp (b10679)** com bibliotecas de runtime **CUDA 13** (`cudart64_13.dll`, `cublas64_13.dll`, `llama-server.exe`) diretamente para a pasta `server/`.

---

### Passo 3: Baixar o Modelo Qwen 3.8 27B (`download_model.ps1`)
Execute o script de download do modelo:
```powershell
powershell -ExecutionPolicy Bypass -File .\setup\download_model.ps1
```
Ou, se preferir baixar manualmente via terminal:
```bash
hf download Qwen/Qwen3.8-27B-GGUF Qwen3.8-27B-Q4_K_M.gguf --local-dir .\models
```
* O arquivo `Qwen3.8-27B-Q4_K_M.gguf` tem aproximadamente **17.77 GB**.

---

### Passo 4: Gerar os Atalhos na Área de Trabalho (`create_shortcuts.ps1`)
```powershell
powershell -ExecutionPolicy Bypass -File .\setup\create_shortcuts.ps1
```
Cria os atalhos numerados e configurados direto no Desktop para facilitar o uso no dia a dia.

---

## 🧠 Esquema da Janela de Contexto

Um dos grandes diferenciais desta configuração é a otimização de memória do **KV Cache** aliada ao **Flash Attention (`-fa on`)** e alocação de slot único (`-np 1`), permitindo alternar entre dois modos:

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

### Comparativo Técnico:

| Parâmetro | Modo Precisão (64k) | Modo Gigante (128k) |
| :--- | :--- | :--- |
| **Comando de Ativação** | `-c 65536 -ctk q8_0 -ctv q8_0` | `-c 131072 -ctk q4_0 -ctv q4_0` |
| **Capacidade de Leitura** | ~50 páginas de código | ~100 páginas de texto/documentação |
| **Precisão de Atenção** | Perfeita para nomes de variáveis e código | Excelente para conversação e resumos |
| **Aceleração** | Flash Attention (`-fa on`) | Flash Attention (`-fa on`) |
| **Uso Total de VRAM** | **~20.6 GB** de 23.4 GB | **~22.6 GB** de 23.4 GB |

> [!IMPORTANT]
> A flag **`-np 1`** foi configurada para evitar que o servidor reserve memória para múltiplos usuários simultâneos, prevenindo erros de alocação no cuBLAS da NVIDIA (`cublasCreate_v2`).

---

## 🖥️ Scripts e Lançadores Disponíveis

Na pasta `scripts/` (e na Área de Trabalho), você encontra:

| Script | Função |
| :--- | :--- |
| **`1-iniciar_servidor_llama.bat`** | **Motor Principal Inteligente:** Detecta o hardware ativo (Dual GPU vs Single GPU) e exibe um menu para você escolher entre **64k (8-bit)** ou **128k (4-bit)**. |
| **`1-iniciar_servidor_128k_gigante.bat`** | **Modo Direto 128k:** Inicia o servidor imediatamente no modo de 128k tokens com 1 clique (perfeito para o Web Chat). |
| **`2-iniciar_aider_com_llama.bat`** | Abre o **Aider (Claude Code Local)** configurado em Português com formato Diff otimizado para o Qwen. Permite arrastar pastas de projetos para cima do ícone. |
| **`3-iniciar_aider_com_lmstudio.bat`** | Conecta o Aider ao servidor visual do **LM Studio** na porta 1234. |
| **`4-iniciar_open_interpreter.bat`** | Abre o **Open Interpreter**, permitindo que a IA execute comandos no PowerShell, liste diretórios e edite arquivos em qualquer pasta do Windows. |

---

## 🌐 Como Conectar ao Web Chat no Navegador

Se você usa interfaces gráficas como **Open WebUI**, **LibreChat** ou extensões de navegador:

1. Inicie o servidor clicando em **`1-iniciar_servidor_llama.bat`** (ou **`1-iniciar_servidor_128k_gigante.bat`**).
2. Na sua interface Web, configure as opções de conexão OpenAI API:
   * **URL Base:** `http://127.0.0.1:8080/v1` (ou `http://localhost:8080/v1`)
   * **API Key:** `none` (qualquer texto é aceito)
   * **Model Name:** `qwen3.8-27b`
3. O chat web responderá imediatamente utilizando o contexto e a aceleração Dual GPU!

---

## 🤖 Como Usar os Agentes de Terminal

### Opção A: Open Interpreter (Controle Total do PC)
* Abra o atalho **`3 - Abrir Agente com Acesso ao PC (Open Interpreter)`**.
* Fale em linguagem natural:
  ```text
  > Liste os arquivos da pasta C:\Projetos e me diga do que se trata o projeto.
  > Crie um script em Python que converte imagens PNG para WebP e execute agora.
  ```
* O agente executa comandos no PowerShell/CMD com a sua autorização e resolve a tarefa sozinho.

### Opção B: Aider (Pair Programmer para Git)
* Pegue a pasta do seu projeto de código e **arraste para cima do atalho `2 - Abrir Claude Code Local (Aider)`**.
* Comandos essenciais no chat:
  * `/add arquivo.py`: Adiciona o arquivo para edição.
  * `/run pytest`: Executa os testes do projeto. Se houver erro, o Qwen corrige o código automaticamente.
  * `/undo`: Desfaz a última modificação no código.

---

## ⚙️ Hardware de Referência

Configuração validada e testada:
* **Placa-Mãe:** MSI MAG Z790 TOMAHAWK
* **GPU 0 (Display Principal):** NVIDIA GeForce RTX 5070 (12 GB GDDR7)
* **GPU 1 (Acelerador Secundário):** NVIDIA GeForce RTX 2080 Ti (11 GB GDDR6)
* **VRAM Combinada:** **23.4 GB**
* **Memória RAM:** 32 GB DDR5
* **Desempenho Médio:** ~35 a 40+ tokens por segundo com 100% de offload na VRAM.
