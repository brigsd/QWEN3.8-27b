# 🤖 Guia Definitivo: IA Local com Qwen 3.8 27B (Dual GPU)

Este ambiente foi configurado para rodar **100% localmente no seu hardware** utilizando a sua **RTX 5070 (12GB) + RTX 2080 Ti (11GB) = 23.4 GB VRAM**.

---

## ⚡ Atalhos na Área de Trabalho

### 🖥️ SERVIDORES (Escolha como quer iniciar o modelo):

1. 🚀 **1 - Iniciar Servidor Qwen 27B**
   * Abre um menu rápido onde você pode escolher:
     * **Apertar ENTER:** Inicia no **Modo Precisão 64k (8-bit KV Cache)** -> Ideal para Código, Aider e Programação.
     * **Digitar 2 e ENTER:** Inicia no **Modo Gigante 128k (4-bit KV Cache)** -> Ideal para Web Chat, Livros e PDFs longos.

2. 📚 **1b - Iniciar Servidor Direto (128k Gigante)**
   * Dá o start direto no **Modo 128k Tokens (4-bit KV Cache + Flash Attention)** com apenas 1 clique, sem perguntar nada.
   * Perfeito quando você vai para o **Web Chat** no navegador conversar sobre documentos imensos.

---

### 🤖 AGENTES (Como interagir com o modelo):

3. 🌐 **No Navegador (Seu Web Chat / Open WebUI):**
   * Conecte na URL: http://127.0.0.1:8080/v1 (API Key: 
one).
   * Ele usará automaticamente o contexto do servidor que estiver aberto (64k ou 128k)!

4. 🤖 **3 - Abrir Agente com Acesso ao PC (Open Interpreter)**
   * Agente com **acesso total ao CMD, PowerShell e Arquivos**.
   * Você pode pedir: *Leia os arquivos da pasta X e me explique* — ele roda comandos sozinho sem precisar de /add.

5. 💻 **2 - Abrir Claude Code Local (Aider)**
   * Agente focado em **repositórios Git e refatoração de código**.
   * Permite arrastar pastas de projetos para cima do atalho.

---

## ⚙️ Comparativo dos Modos de Contexto:

| Modo | Tamanho da Janela | Quantização do Cache | Uso Máximo de VRAM | Melhor Para |
| :--- | :--- | :--- | :--- | :--- |
| **Precisão (8-bit)** | **64.000 tokens** (~50 páginas) | q8_0 (Perda < 0.01%) | **~20.6 GB** (sobra ~2.8 GB) | Programação, testes, refatoração de código sem falha em sintaxe. |
| **Gigante (4-bit)** | **128.000 tokens** (~100 páginas) | q4_0 (Perda ~2%) | **~22.6 GB** (sobra ~0.8 GB) | Web Chat, leitura de múltiplos PDFs, livros inteiros, documentações extensas. |

Ambos os modos rodam **100% dentro da VRAM das suas duas placas de vídeo**, utilizando **Flash Attention (-fa on)** para velocidade máxima!
