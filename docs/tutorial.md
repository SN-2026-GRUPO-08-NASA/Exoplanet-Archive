# Tutorial de replicação

## 1. Serviços

Crie a organização GitHub `SN-2026-GRUPO-08-NASA`, o repositório público `Exoplanet-Archive` e o projeto Supabase `Exoplanet-Archive-DB`, na região South America (São Paulo). Convide o professor conforme o enunciado.

## 2. Banco de dados

Abra o SQL Editor do Supabase e execute todo o conteúdo de `sql/setup.sql`. Ele cria as tabelas `exoplanetas` e `execucoes`, define a chave única `pl_name`, RLS, políticas públicas de leitura e permissões para o `service_role`.

## 3. Credenciais

Em GitHub > Settings > Secrets and variables > Actions, adicione as Variables `SUPABASE_URL` e `SUPABASE_ANON_KEY`. Adicione como Secret somente `SUPABASE_SERVICE_ROLE_KEY`. O workflow de publicação gera `config.js` no artefato do Pages usando as Variables; a service role nunca vai para HTML, commits ou logs.

## 4. Coleta

Em Actions, execute manualmente o workflow **Atualizar dados da NASA**. Ele consulta o endpoint TAP do Exoplanet Archive na tabela `pscomppars`, deduplica os resultados por nome do planeta e faz upsert em lotes. Uma linha em `execucoes` registra a situação da execução.

## 5. Painel

Em Settings > Pages, selecione **GitHub Actions**. Execute o workflow **Publicar painel**. Ele gera a configuração pública somente no artefato publicado; o painel consulta a API REST, traz a data da última execução e permite filtrar por método de descoberta.

## Validação final

- Confirme uma execução verde no Actions.
- Confira registros em `exoplanetas` e um log concluído em `execucoes`.
- Abra o GitHub Pages e teste o seletor.
- Copie links e capturas solicitadas para o PDF da entrega.
