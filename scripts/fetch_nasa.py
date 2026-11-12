import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
BATCH_SIZE = 500
TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
QUERY = """select pl_name,hostname,discoverymethod,disc_year,pl_orbper,
pl_rade,pl_bmasse,sy_dist,ra,dec,disc_pubdate from pscomppars"""


def request_json(url, method="GET", payload=None, extra_headers=None):
    headers = {"Accept": "application/json"}
    headers.update(extra_headers or {})
    body = json.dumps(payload).encode() if payload is not None else None
    if body:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method=method)
    with urlopen(request, timeout=90) as response:
        content = response.read().decode("utf-8")
        return json.loads(content) if content else None


def supabase_headers(prefer=None):
    headers = {"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}"}
    if prefer:
        headers["Prefer"] = prefer
    return headers


def normalize(item):
    publication_date = item.get("disc_pubdate")
    return {
        "pl_name": item["pl_name"],
        "hostname": item.get("hostname"),
        "discovery_method": item.get("discoverymethod"),
        "discovery_year": item.get("disc_year"),
        "orbital_period_days": item.get("pl_orbper"),
        "planet_radius_earth": item.get("pl_rade"),
        "planet_mass_earth": item.get("pl_bmasse"),
        "distance_pc": item.get("sy_dist"),
        "ra": item.get("ra"),
        "dec": item.get("dec"),
        # A NASA fornece apenas ano e mês de publicação; usar o primeiro dia
        # cria um valor válido para a coluna timestamptz do Supabase.
        "source_updated_at": (
            f"{publication_date}-01T00:00:00+00:00" if publication_date else None
        ),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    if not SUPABASE_URL or not SERVICE_KEY:
        raise RuntimeError("Defina SUPABASE_URL e SUPABASE_SERVICE_KEY nos Secrets/ambiente.")

    executions = f"{SUPABASE_URL}/rest/v1/execucoes"
    run = request_json(
        executions,
        "POST",
        {"status": "erro_critico"},
        supabase_headers("return=representation"),
    )[0]
    processed = batches = errors = 0
    try:
        params = urlencode({"query": QUERY, "format": "json"})
        source = request_json(f"{TAP_URL}?{params}")
        records = {
            row["pl_name"]: normalize(row)
            for row in source
            if row.get("pl_name")
        }
        values = list(records.values())
        endpoint = f"{SUPABASE_URL}/rest/v1/exoplanetas?on_conflict=pl_name"
        for start in range(0, len(values), BATCH_SIZE):
            batch = values[start:start + BATCH_SIZE]
            batches += 1
            try:
                request_json(
                    endpoint,
                    "POST",
                    batch,
                    supabase_headers("resolution=merge-duplicates,return=minimal"),
                )
                processed += len(batch)
            except (HTTPError, URLError, ValueError) as exc:
                errors += 1
                print(f"Falha no lote {batches}: {exc}", file=sys.stderr)
        status = "erro_parcial" if errors else "concluido"
        detail = f"{errors} lote(s) falharam" if errors else None
    except (HTTPError, URLError, ValueError, RuntimeError) as exc:
        status, errors, detail = "erro_critico", 1, str(exc)
        print(f"Falha no pipeline: {detail}", file=sys.stderr)
    finally:
        payload = {
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "registros_processados": processed,
            "lotes": batches,
            "erros": errors,
            "status": status,
            "detalhe_erro": detail,
        }
        request_json(
            f"{executions}?id=eq.{run['id']}",
            "PATCH",
            payload,
            supabase_headers("return=minimal"),
        )
    if status != "concluido":
        sys.exit(1)
    print(f"Concluído: {processed} registros em {batches} lote(s).")


if __name__ == "__main__":
    main()
