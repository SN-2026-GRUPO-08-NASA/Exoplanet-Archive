# Exoplanet Archive - Grupo 08

Pipeline que coleta dados confirmados de exoplanetas do NASA Exoplanet Archive, normaliza os registros e os grava no Supabase. O painel estático consulta a API REST pública do Supabase e pode ser publicado no GitHub Pages.

## Arquitetura

`NASA Exoplanet Archive (TAP) -> GitHub Actions -> Supabase -> GitHub Pages`

O workflow executa diariamente e também pode ser disparado manualmente. A coleta usa a tabela `pscomppars`, remove duplicidades por `pl_name` e faz upsert em lotes.

## Configuração

1. Crie a organização `SN-2026-GRUPO-08-NASA`, o repositório público `Exoplanet-Archive` e o projeto Supabase `Exoplanet-Archive-DB` na região South America (São Paulo).
2. Convide `GilFerques` na organização GitHub e `rafael.ferques@ifpr.edu.br` como Developer no projeto Supabase.
3. No SQL Editor do Supabase, execute [`sql/setup.sql`](sql/setup.sql).
4. Em GitHub > Settings > Secrets and variables > Actions, cadastre:
   - **Variables:** `SUPABASE_URL` e `SUPABASE_ANON_KEY` (URL e chave publishable/anon, ambas públicas no painel).
   - **Secret:** `SUPABASE_SERVICE_ROLE_KEY` (chave administrativa; nunca a coloque em arquivos, logs ou no painel).
5. Em Settings > Pages, selecione **GitHub Actions** como fonte de publicação.
6. Rode o workflow **Atualizar dados da NASA** manualmente uma vez e verifique os dados no Table Editor. Depois, execute **Publicar painel**.

## Execução local

Defina as variáveis de ambiente e execute:

```powershell
$env:SUPABASE_URL = 'https://SEU-PROJETO.supabase.co'
$env:SUPABASE_SERVICE_KEY = 'sua-service-role-key'
python scripts/fetch_nasa.py
```

O script usa apenas a biblioteca padrão do Python.

## Segurança

- A `SUPABASE_SERVICE_ROLE_KEY` fica exclusivamente nos Secrets do GitHub Actions.
- `SUPABASE_URL` e `SUPABASE_ANON_KEY` ficam como Variables; elas são públicas por natureza no navegador e têm apenas acesso de leitura, protegido por RLS.
- Valores da API são escapados com `escapeHtml()` antes de entrar no HTML.

## Links da entrega

- Organização GitHub: _adicionar link definitivo_
- Repositório: _adicionar link definitivo_
- Painel GitHub Pages: _adicionar link definitivo_
- API REST Supabase: `https://SEU-PROJETO.supabase.co/rest/v1/exoplanetas?select=*`

Consulte [`docs/tutorial.md`](docs/tutorial.md) para o guia completo de replicação e [`docs/ai-interaction.md`](docs/ai-interaction.md) para o registro de uso de IA.
