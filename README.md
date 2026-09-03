# 🚀 Ecossistema Local de IA: Qwen 3.8 27B Supreme Edition (Dual GPU)

Ambiente de execução local de alta performance para o modelo de fronteira **Qwen 3.8 27B**, com aceleração por **Dual GPU (RTX 5070 12GB + RTX 2080 Ti 11GB = 23.4 GB VRAM)**, quantização de contexto calibrada (**64k com Visão Multimodal e 128k Contexto Gigante**), motor de busca **BM25**, gerenciador **MCP Dinâmico (`/mcp`)**, **Skills de Engenharia** e **3 Modos de Raciocínio (`Shift+Tab`)**.

---

## 📑 Índice
1. [🖥️ Os 3 Atalhos Definitivos na Área de Trabalho](#️-os-3-atalhos-definitivos-na-área-de-trabalho)
2. [🎛️ Modos de Execução do Servidor (Dual GPU)](#️-modos-de-execução-do-servidor-dual-gpu)
3. [🧠 Os 3 Modos de Raciocínio (Alternáveis via Shift+Tab)](#-os-3-modos-de-raciocínio)
4. [🚀 Skills Especializadas de Engenharia](#-skills-especializadas-de-engenharia)
5. [🤖 Agente Nativo com Tool Calling & BM25](#-agente-nativo-com-tool-calling--bm25)
6. [🔌 MCP Dinâmico (`/mcp`)](#-mcp-dinâmico-mcp)

---

## 🖥️ Os 3 Atalhos Definitivos na Área de Trabalho

Organizamos todo o ecossistema em **apenas 3 atalhos numerados e elegantes**:

```
 ┌────────────────────────────────────────────────────────┐
 │ 1 - Iniciar Servidor Qwen 27B (Dual GPU)               │ ──► Sobe o servidor llama.cpp (64k com Visão ou 128k Gigante)
 ├────────────────────────────────────────────────────────┤
 │ 2 - Abrir Agente Nativo de Desenvolvimento             │ ──► Agente de Código com BM25, MCP, Skills e Shift+Tab
 ├────────────────────────────────────────────────────────┤
 │ 3 - Central de Ferramentas e Benchmarks                │ ──► Bateria de Testes (LiveCodeBench), Aider, Doctor e Web Chat
 └────────────────────────────────────────────────────────┘
```

---

## 🎛️ Modos de Execução do Servidor (Dual GPU)

O servidor calibrado permite alternar a janela de contexto com 1 clique:

| Opção no Menu | Modo | Janela de Contexto | VRAM Utilizada | Velocidade | Melhor Uso |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **[1]** | **Precisão 64k (8-bit KV + Visão)** | 65.536 Tokens | ~21.0 GB / 23.4 GB | **~40 tok/s** | **RECOMENDADO** (Programação, refatoração, análise de imagens e precisão máxima) |
| **[2]** | **Gigante 128k (4-bit KV Puro)** | 131.072 Tokens | ~21.5 GB / 23.4 GB | **~35 tok/s** | Projetos gigantes, documentação pesada e múltiplos repositórios |

---

## 🧠 Os 3 Modos de Raciocínio

Pressione **`Shift + Tab`** ou **`F2`** no prompt do agente para alternar em tempo real:

* **`[⚡ NORMAL]` (Min-P 0.05):** Respostas rápidas e código cirúrgico sem alucinações de sintaxe.
* **`[🧠 PENSAMENTO]` (Deep Think):** Constrói uma análise lógica prévia em um painel destacado antes de emitir a solução.
* **`[🛡️ REFLEXÃO]` (Auto-Crítica):** Gera a solução e roda uma auditoria interna para corrigir race conditions, ponteiros nulos e erros de concorrência.

---

## 🚀 Skills Especializadas de Engenharia

| Comando | Skill | Função |
| :--- | :--- | :--- |
| **`/doctor`** | 🩺 **Doctor** | Checkup de VRAM das duas placas (RTX 5070 + 2080 Ti), temperaturas e porta 8080. |
| **`/review <alvo>`** | 🔍 **Code Review** | Auditoria sênior de código com severidade (🔴 Alta, 🟡 Média, 🟢 Baixa) e linhas. |
| **`/security <alvo>`** | 🛡️ **Security Review** | Auditoria de segurança OWASP (vazamento de tokens, injeção, caminhos inseguros). |
| **`/simplify <alvo>`** | ✂️ **Simplify** | Refatoração limpa para eliminar código morto e achatar lógica aninhada. |
| **`/verify [pasta]`** | 🧪 **Verify** | Executa os testes do projeto (`pytest`, `npm test`, `cargo`) e analisa falhas. |

---

## 🔌 MCP Dinâmico (`/mcp`)

* `/mcp list`: Exibe ferramentas e status (🟢 ATIVO / ⚪ DESLIGADO).
* `/mcp on mecanifica`: Habilita ferramentas CAD 3D do Mecanifica.
* `/mcp on web`: Habilita busca em tempo real no DuckDuckGo.
* `/mcp off [nome]`: Desliga módulos e zera resíduos de contexto.
