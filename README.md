# 🚀 Ecossistema Local de IA: Qwen 3.8 27B & GLM (Dual GPU)

Ambiente de execução local de alta performance para modelos de fronteira (**Qwen 3.8 27B** e **GLM**), com aceleração por **Dual GPU (RTX 5070 + RTX 2080 Ti = 23.4 GB VRAM)**, quantização de contexto flexível (**16-bit FP16, 8-bit Q8_0 e 4-bit Q4_0**), motor de busca **BM25**, gerenciador **MCP Dinâmico (`/mcp`)**, **Skills de Engenharia** e **3 Modos de Raciocínio (`Shift+Tab`)**.

---

## 📑 Índice
1. [🖥️ Os 3 Atalhos Definitivos na Área de Trabalho](#️-os-3-atalhos-definitivos-na-área-de-trabalho)
2. [🎛️ Suporte ao GLM com Seletor 16-bit vs 8-bit](#️-suporte-ao-glm-com-seletor-16-bit-vs-8-bit)
3. [🧠 Os 3 Modos de Raciocínio (Alternáveis via Shift+Tab)](#-os-3-modos-de-raciocínio)
4. [🚀 Skills Especializadas de Engenharia](#-skills-especializadas-de-engenharia)
5. [🤖 Agente Nativo com Tool Calling & BM25](#-agente-nativo-com-tool-calling--bm25)
6. [🔌 MCP Dinâmico (`/mcp`)](#-mcp-dinâmico-mcp)

---

## 🖥️ Os 3 Atalhos Definitivos na Área de Trabalho

Organizamos todo o ecossistema em **apenas 3 atalhos numerados e elegantes**:

```
 ┌────────────────────────────────────────────────────────┐
 │ 1 - Iniciar Servidor de IA (Qwen ou GLM)              │ ──► Sobe o Qwen (64k/128k/Turbo) ou GLM (16/8/4-bit)
 ├────────────────────────────────────────────────────────┤
 │ 2 - Abrir Agente Nativo de Desenvolvimento             │ ──► Agente de Código com BM25, MCP, Skills e Shift+Tab
 ├────────────────────────────────────────────────────────┤
 │ 3 - Central de Ferramentas e Benchmarks                │ ──► Bateria de Testes (LiveCodeBench), Aider e Doctor
 └────────────────────────────────────────────────────────┘
```

---

## 🎛️ Suporte ao GLM com Seletor 16-bit vs 8-bit

O servidor unificado permite alternar o modelo e a precisão do KV Cache com 1 clique:

| Opção no Menu | Modelo | Janela de Contexto (KV Cache) | Economia de Memória |
| :--- | :--- | :--- | :---: |
| **[1]** | **Qwen 27B** | 64k Tokens (8-bit Q8_0) | **Recomendado** (Folga de 2.8 GB VRAM) |
| **[2]** | **Qwen 27B** | 128k Tokens (4-bit Q4_0) | Contexto Gigante |
| **[3]** | **Qwen 27B** | Modo TURBO Especulativo (Draft 0.5B) | Aceleração para ~60-75 tok/s |
| **[4]** | **GLM** | 16-bit FP16 | Precisão Máxima Original |
| **[5]** | **GLM** | 8-bit Q8_0 | **Otimizado:** Metade da VRAM com perda ZERO |
| **[6]** | **GLM** | 4-bit Q4_0 | Contexto Ultra Longo |

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
