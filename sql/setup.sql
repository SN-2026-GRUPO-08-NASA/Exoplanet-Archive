create table if not exists public.exoplanetas (
  id bigint generated always as identity primary key,
  pl_name text not null,
  hostname text,
  discovery_method text,
  discovery_year integer,
  orbital_period_days numeric,
  planet_radius_earth numeric,
  planet_mass_earth numeric,
  distance_pc numeric,
  ra numeric,
  dec numeric,
  source_updated_at timestamptz,
  collected_at timestamptz not null default now(),
  constraint exoplanetas_pl_name_key unique (pl_name)
);

create table if not exists public.execucoes (
  id bigint generated always as identity primary key,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  registros_processados integer not null default 0,
  lotes integer not null default 0,
  erros integer not null default 0,
  status text not null check (status in ('concluido', 'erro_parcial', 'erro_critico')),
  detalhe_erro text
);

alter table public.exoplanetas enable row level security;
alter table public.execucoes enable row level security;

drop policy if exists "leitura publica exoplanetas" on public.exoplanetas;
create policy "leitura publica exoplanetas"
on public.exoplanetas for select to anon, authenticated using (true);

drop policy if exists "leitura publica execucoes" on public.execucoes;
create policy "leitura publica execucoes"
on public.execucoes for select to anon, authenticated using (true);

grant usage on schema public to anon, authenticated, service_role;
grant select on public.exoplanetas, public.execucoes to anon, authenticated;
grant all on public.exoplanetas, public.execucoes to service_role;
grant usage, select on all sequences in schema public to service_role;
