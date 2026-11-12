# Histórico de Interação com IA

> Registre todos os prompts utilizados durante o desenvolvimento, inclusive os que não funcionaram.

---

## Informações gerais

| Campo | Valor |
| - | - |
| **Grupo** | Grupo 08 |
| **Integrantes** | Carlos Seibert, Matheus Broring e Samuel Barzotto |
| **API NASA escolhida** | NASA Exoplanet Archive (TAP) |
| **IA utilizada** | ChatGPT (Codex) |
| **Data de início** | 30/09/2026|
| **Data de conclusão** | 12/11/2026 |

---

## Interação 1 — Estrutura inicial do pipeline

**Data:** 30/09/2026  
**Objetivo:** Criar a estrutura inicial para coleta, armazenamento e visualização de dados de exoplanetas.

**Prompt enviado à IA:**

```
Crie uma estrutura inicial para um pipeline Python que consulta a NASA Exoplanet Archive,
faz upsert em Supabase, registra execuções e disponibiliza um painel estático seguro.
```

**Resumo da resposta:**
Foi proposta uma estrutura com um script Python para consultar a API TAP da NASA, tabelas no Supabase para os exoplanetas e as execuções do pipeline, um workflow do GitHub Actions e um painel estático para consulta dos dados.

**O que funcionou:**
A estrutura inicial foi aproveitada para organizar o script `fetch_nasa.py`, o arquivo SQL, os workflows e o painel.

**O que precisou ajuste:**
O grupo revisou a proposta e ajustou a chave natural para `pl_name`, manteve a chave `service_role` apenas nos Secrets do GitHub Actions e adicionou RLS com leitura pública no Supabase.

---

## Interação 2 — Configuração do Supabase e GitHub Actions

**Data:** 05/11/2026 
**Objetivo:** Identificar as configurações necessárias para executar a coleta automática com segurança.

**Prompt enviado à IA:**

```
O que ainda falta configurar no Supabase, no GitHub Actions e no GitHub Pages para o pipeline funcionar?
```

**Resumo da resposta:**
Foram indicadas as etapas de executar o SQL no Supabase, cadastrar as variáveis `SUPABASE_URL` e `SUPABASE_ANON_KEY`, cadastrar o Secret `SUPABASE_SERVICE_ROLE_KEY`, executar o workflow de coleta e publicar o painel pelo GitHub Pages.

**O que funcionou:**
A separação entre variáveis públicas e a chave administrativa foi usada na configuração dos workflows.

**O que precisou ajuste:**
As chaves e a URL reais precisam ser preenchidas diretamente nas configurações do projeto; elas não devem ser registradas neste documento nem em arquivos públicos.

## Resumo final

**Total de interações:** 2

**Principais contribuições da IA:**

* Estrutura inicial do pipeline de coleta e persistência dos dados.
* Orientação para configurar Supabase, GitHub Actions e GitHub Pages de forma segura.

**Principais limitações encontradas:**

* A IA não substitui a validação das credenciais, permissões e respostas reais da API.
* As configurações precisam ser testadas no projeto do grupo.

**Avaliação geral do uso da IA:**
A IA ajudou a acelerar a organização inicial do projeto e a esclarecer as configurações necessárias. As sugestões foram revisadas pelo grupo, que permaneceu responsável por testar o código, proteger credenciais, executar o SQL e validar os resultados no Supabase e no painel.
