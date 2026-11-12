
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

QUERY = """
SELECT pl_name, hostname, discoverymethod, disc_year,
pl_orbper, pl_rade, pl_bmasse, sy_dist, ra, dec, disc_pubdate
FROM pscomppars
"""


def request_json(url, method="GET", payload=None, extra_headers=None):
    headers = {"Accept": "application/json"}
    headers.update(extra_headers or {})

    body = json.dumps(payload).encode("utf-8") if payload is not None else None

    if body is not None:
        headers["Content-Type"] = "application/json"

    request = Request(
        url,
        data=body,
        headers=headers,
        method=method
    )

    try:
        with urlopen(request, timeout=120) as response:
            content = response.read().decode("utf-8")
            return json.loads(content) if content else None

    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"HTTP {exc.code}: {error_body}"
        ) from exc

    except URLError as exc:
        raise RuntimeError(
            f"Erro de conexão: {exc.reason}"
        ) from exc


def supabase_headers(prefer=None):
    headers = {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}"
    }

    if prefer:
        headers["Prefer"] = prefer

    return headers


def normalize_publication_date(value):
    if not value:
        return None

    value = str(value).strip()

    for date_format in ("%Y-%m", "%Y-%m-%d"):
        try:
            date = datetime.strptime(value, date_format)
            return date.replace(
                tzinfo=timezone.utc
            ).isoformat()
        except ValueError:
            continue

    return None


def normalize(item):
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
        "source_updated_at": normalize_publication_date(
            item.get("disc_pubdate")
        ),
        "collected_at": datetime.now(timezone.utc).isoformat()
    }


def main():
    if not SUPABASE_URL or not SERVICE_KEY:
        raise RuntimeError(
            "Configure SUPABASE_URL e SUPABASE_SERVICE_KEY."
        )

    processed = 0
    batches = 0
    errors = 0
    detail = None
    status = "erro_critico"
    run = None

    executions = f"{SUPABASE_URL}/rest/v1/execucoes"

    try:
        result = request_json(
            executions,
            "POST",
            {"status": "em_andamento"},
            supabase_headers("return=representation")
        )

        if not result:
            raise RuntimeError(
                "Não foi possível registrar a execução no Supabase."
            )

        run = result[0]

        params = urlencode({
            "query": QUERY,
            "format": "json"
        })

        source = request_json(f"{TAP_URL}?{params}")

        if not isinstance(source, list):
            raise RuntimeError(
                "A NASA retornou um formato de dados inesperado."
            )

        records = {
            row["pl_name"]: normalize(row)
            for row in source
            if row.get("pl_name")
        }

        values = list(records.values())

        endpoint = (
            f"{SUPABASE_URL}/rest/v1/exoplanetas"
            "?on_conflict=pl_name"
        )

        print(f"Registros encontrados: {len(values)}")

        for start in range(0, len(values), BATCH_SIZE):
            batch = values[start:start + BATCH_SIZE]
            batches += 1

            try:
                request_json(
                    endpoint,
                    "POST",
                    batch,
                    supabase_headers(
                        "resolution=merge-duplicates,return=minimal"
                    )
                )

                processed += len(batch)

                print(
                    f"Lote {batches} concluído: {len(batch)} registros."
                )

            except Exception as exc:
                errors += 1

                print(
                    f"Falha no lote {batches}: {exc}",
                    file=sys.stderr
                )

        status = "erro_parcial" if errors else "concluido"

        if errors:
            detail = f"{errors} lote(s) falharam."

    except Exception as exc:
        status = "erro_critico"
        errors += 1
        detail = str(exc)

        print(
            f"Falha no pipeline: {detail}",
            file=sys.stderr
        )

    finally:
        if run:
            payload = {
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "registros_processados": processed,
                "lotes": batches,
                "erros": errors,
                "status": status,
                "detalhe_erro": detail
            }

            try:
                request_json(
                    f"{executions}?id=eq.{run['id']}",
                    "PATCH",
                    payload,
                    supabase_headers("return=minimal")
                )

            except Exception as exc:
                print(
                    f"Erro ao atualizar histórico: {exc}",
                    file=sys.stderr
                )
                status = "erro_critico"

    if status != "concluido":
        sys.exit(1)

    print(
        f"Pipeline concluído: {processed} registros "
        f"em {batches} lote(s)."
    )


if __name__ == "__main__":
    main()
