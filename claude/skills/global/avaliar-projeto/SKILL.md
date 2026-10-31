---
name: avaliar-projeto
description: Avalia um projeto de software nos critérios de Segurança, Clareza e Manutenibilidade, mapeando também a stack utilizada. Por padrão gera o arquivo AVALIACAO.md na raiz do projeto. Use '--chat' ou 'pelo chat' para receber a avaliação diretamente no chat sem criar arquivo.
disable-model-invocation: true
---

# Avaliar Projeto

Você é um engenheiro de software sênior avaliando um projeto recebido de terceiros. Seu objetivo é produzir um relatório técnico acessível a gestores não-técnicos.

## Passo 1 — Determinar o modo de saída

Verifique o valor de `args`:

- Se `args` contiver `--chat` ou `pelo chat` (em qualquer combinação de maiúsculas/minúsculas): **modo chat** — escreva a avaliação completa de volta no chat, sem criar nenhum arquivo.
- Caso contrário: **modo arquivo** — crie ou atualize o arquivo `AVALIACAO.md` na raiz do projeto atual.

**Se o modo for arquivo**, verifique se já existe um arquivo `AVALIACAO.md` na raiz antes de prosseguir. Se existir, **interrompa e pergunte ao usuário** o que deseja fazer, com as seguintes opções:
1. Sobrescrever o arquivo existente.
2. Criar com nome alternativo (ex: `AVALIACAO-2.md`).
3. Cancelar.

Aguarde a resposta antes de continuar.

## Passo 2 — Ler o projeto

Leia os arquivos do projeto na seguinte ordem de prioridade (ignore `node_modules/`, `dist/`, `.git/`):

1. `package.json` — dependências, scripts, stack.
2. Arquivo principal do servidor (ex: `server.ts`, `server.js`, `api/`, `backend/`).
3. Arquivo principal do frontend (ex: `App.tsx`, `main.tsx`, `index.tsx`).
4. Arquivos de configuração: `.gitignore`, `vite.config.ts`, `tsconfig.json`.
5. Arquivos de serviço (`services/`) e integrações externas.
6. Demais arquivos de código relevantes.

Se existir um arquivo `CRITERIO.md` na raiz do projeto, leia-o também — ele pode conter critérios adicionais específicos deste projeto.

## Passo 3 — Mapear a Stack

Identifique as tecnologias usadas e organize em uma tabela com as colunas **Camada**, **Tecnologia** e **Função**. Cubra as seguintes camadas quando presentes:

- Frontend (framework + linguagem)
- Estilização (CSS, Tailwind, etc.)
- Bundler (Vite, Webpack, etc.)
- Backend / Servidor
- Runtime TypeScript (tsx, ts-node, Bun, etc.)
- IA Generativa (provedor e SDK)
- Bibliotecas principais com função clara
- Fontes de dados externas (APIs, RSS, banco de dados)

## Passo 4 — Avaliar os três critérios

Para cada critério, atribua uma **nota de 0 a 10**, liste pontos positivos e monte uma tabela de pontos de atenção com colunas **Risco**, **Gravidade** (🔴 Alta / 🟡 Média / 🟢 Baixa) e **Descrição**.

---

### Critério 1 — Segurança

Verifique:
- Chaves de API estão em variáveis de ambiente e **não** escritas diretamente no código?
- O arquivo `.env` (ou equivalente) está listado no `.gitignore` e protegido de envio acidental ao repositório?
- Se há servidor intermediário, ele impede que chaves sejam expostas ao navegador?
- Endpoints que aceitam URLs ou inputs externos fazem validação antes de processá-los?
- Há algum mecanismo de limite de requisições (rate limiting)?
- O servidor tem autenticação, ou qualquer pessoa na rede pode usá-lo?

Referências de nota: 8–10 = boas práticas atendidas | 5–7 = chaves protegidas mas com vulnerabilidades pontuais | 0–4 = chave exposta ou sem proteção básica.

---

### Critério 2 — Clareza

Verifique:
- Nomes de arquivos, componentes, funções e variáveis descrevem bem o que fazem?
- Há separação de responsabilidades (visual separado de lógica, serviços separados)?
- Existe arquivo de tipos/interfaces documentando as estruturas de dados?
- Constantes e configurações estão centralizadas?
- Existe documentação de uso (README, comentários, página "Sobre")?
- Existe `.env.example` ou equivalente?
- Há comentários explicando lógica não-óbvia?

Referências de nota: 8–10 = código autodescritivo com documentação | 5–7 = legível mas com lacunas | 0–4 = difícil de navegar, sem documentação.

---

### Critério 3 — Manutenibilidade

Verifique:
- O projeto usa TypeScript ou tipagem equivalente de forma consistente?
- Existem testes automatizados? Se não, quais são os riscos concretos?
- Há arquivos ou componentes com responsabilidades demais (muito longos, misturando lógica e visual)?
- Existem valores duplicados ou inconsistentes no código?
- O `package-lock.json` ou `yarn.lock` está presente?
- Há bugs latentes identificáveis por leitura estática (closures desatualizadas, tratamento de erro ausente, condições de corrida)?

Referências de nota: 8–10 = tipagem consistente, testes presentes, arquivos coesos | 5–7 = tipagem presente, sem testes, organizado | 0–4 = sem tipagem, sem testes, difícil de modificar.

## Passo 5 — Montar o relatório

Use exatamente a estrutura abaixo. Escreva em **português brasileiro**. Inclua no glossário todos os termos técnicos usados no corpo do relatório.

```
# Avaliação Técnica — [Nome do Projeto]

> **Para quem é este documento:** Gestores e tomadores de decisão com conhecimento básico de tecnologia. Um glossário está disponível ao final para termos técnicos marcados com *.

---

## Stack Utilizada

| Camada | Tecnologia | Função |
|---|---|---|
...

---

## 1. Segurança

**Nota: X/10 — [frase resumindo o estado geral]**

### O que está correto
- ...

### Pontos de atenção

| Risco | Gravidade | Descrição |
|---|---|---|
...

---

## 2. Clareza

[mesma estrutura]

---

## 3. Manutenibilidade

[mesma estrutura]

---

## Resumo Executivo

| Dimensão | Nota | Status |
|---|---|---|
| Segurança | X/10 | ✅ ou ⚠️ |
| Clareza | X/10 | ✅ ou ⚠️ |
| Manutenibilidade | X/10 | ✅ ou ⚠️ |

[Parágrafo de 3–5 linhas listando as prioridades mais urgentes]

---

## Glossário

| Termo | Definição |
|---|---|
...
```

Use ✅ no status quando a nota for ≥ 7, e ⚠️ quando for < 7.

## Passo 6 — Entregar

- **Modo arquivo:** Salve o conteúdo em `AVALIACAO.md` na raiz do projeto e informe ao usuário que o arquivo foi criado, com um resumo de uma linha por critério.
- **Modo chat:** Escreva o relatório completo diretamente na resposta.
