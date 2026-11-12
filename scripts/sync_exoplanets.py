import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get(
    "SUPABASE_SERVICE_ROLE_KEY", ""
)

BATCH_SIZE = 500
TAP_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

QUERY = """
SELECT pl_name, hostname, discoverymethod, disc_year,
       pl_orbper, pl_rade, pl_bmasse, sy_dist,
       ra, dec, disc_pubdate
FROM pscomppars
"""


def request_json(url, method="GET", payload=None, extra_headers=None):
    headers = {"Accept": "application/json"}
    headers.update(extra_headers or {})

    body = None

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
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

    except Exception as exc:
        if hasattr(exc, "read"):
            error_body = exc.read().decode(
                "utf-8", errors="replace"
            )
            raise RuntimeError(
                f"Erro na requisição {method} {url}: {error_body}"
            ) from exc

        raise RuntimeError(
            f"Erro na requisição {method} {url}: {exc}"
        ) from exc


def supabase_headers(prefer=None):
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
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

    print(
        f"Data de publicação inválida: {value}",
        file=sys.stderr
    )

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
    if not SUPABASE_URL:
        raise RuntimeError(
            "SUPABASE_URL não encontrada nas GitHub Variables."
        )

    if not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY não encontrada nos GitHub Secrets."
        )

    processed = 0
    batches = 0
    errors = 0
    detail = None
    status = "erro_critico"
    run = None

    executions = f"{SUPABASE_URL}/rest/v1/execucoes"

    try:
        print("Registrando execução no Supabase...")

        result = request_json(
            executions,
            method="POST",
            payload={"status": "erro_critico"},
            extra_headers=supabase_headers("return=representation")
        )

        if not isinstance(result, list) or not result:
            raise RuntimeError(
                "Não foi possível criar o registro de execução."
            )

        run = result[0]

        if "id" not in run:
            raise RuntimeError(
                "O registro de execução não retornou um ID."
            )

        print("Consultando NASA Exoplanet Archive...")

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

        print(f"Exoplanetas encontrados: {len(values)}")

        endpoint = (
            f"{SUPABASE_URL}/rest/v1/exoplanetas"
            "?on_conflict=pl_name"
        )

        for start in range(0, len(values), BATCH_SIZE):
            batch = values[start:start + BATCH_SIZE]
            batches += 1

            try:
                request_json(
                    endpoint,
                    method="POST",
                    payload=batch,
                    extra_headers=supabase_headers(
                        "resolution=merge-duplicates,return=minimal"
                    )
                )

                processed += len(batch)

                print(
                    f"Lote {batches} concluído: "
                    f"{len(batch)} registros."
                )

            except Exception as exc:
                errors += 1

                print(
                    f"Falha no lote {batches}: {exc}",
                    file=sys.stderr
                )

        if errors:
            status = "erro_parcial"
            detail = f"{errors} lote(s) falharam."
        else:
            status = "concluido"

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
                    method="PATCH",
                    payload=payload,
                    extra_headers=supabase_headers("return=minimal")
                )

                print("Histórico de execução atualizado.")

            except Exception as exc:
                status = "erro_critico"

                print(
                    f"Falha ao atualizar histórico: {exc}",
                    file=sys.stderr
                )

    if status != "concluido":
        sys.exit(1)

    print(
        f"Sincronização concluída! "
        f"{processed} registros processados "
        f"em {batches} lote(s)."
    )


if __name__ == "__main__":
    main()
