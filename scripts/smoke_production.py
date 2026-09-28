from __future__ import annotations

import argparse
import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _request(base_url: str, path: str) -> tuple[int, dict[str, str], bytes]:
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        headers={"User-Agent": "mercado-tech-brasil-production-smoke/1"},
    )
    with urlopen(request, timeout=20) as response:
        return (
            int(response.status),
            {key.lower(): value for key, value in response.headers.items()},
            response.read(),
        )


def _json(base_url: str, path: str) -> tuple[dict[str, Any], dict[str, str]]:
    status, headers, body = _request(base_url, path)
    if status != 200:
        raise RuntimeError(f"{path}: HTTP {status}")
    payload = json.loads(body.decode("utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path}: resposta JSON não é objeto.")
    return payload, headers


def validate(
    *,
    base_url: str,
    expected_version: str,
    expected_monthly: str,
    expected_rais_year: int,
) -> dict[str, object]:
    health, health_headers = _json(base_url, "/api/v1/system/health")
    if health.get("status") != "ok":
        raise RuntimeError("Health não retornou status=ok.")
    if health.get("version") != expected_version:
        raise RuntimeError(
            f"Versão em produção divergente: {health.get('version')!r}."
        )

    expected_headers = {
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "referrer-policy": "strict-origin-when-cross-origin",
        "permissions-policy": "camera=(), microphone=(), geolocation=()",
        "cross-origin-opener-policy": "same-origin",
        "content-security-policy": "default-src 'self'",
    }
    for key, value in expected_headers.items():
        actual = health_headers.get(key, "")
        if value not in actual:
            raise RuntimeError(
                f"Header de segurança divergente: {key}="
                f"{actual!r}."
            )

    hsts = health_headers.get("strict-transport-security", "")
    if "max-age=31536000" not in hsts or "includeSubDomains" not in hsts:
        raise RuntimeError(f"HSTS ausente ou divergente: {hsts!r}.")

    readiness, _ = _json(base_url, "/api/v1/system/readiness")
    if readiness.get("api") != "ready" or readiness.get("data_loaded") is not True:
        raise RuntimeError("Readiness não confirmou dados publicados.")
    if readiness.get("published_competence") != expected_monthly:
        raise RuntimeError("Readiness aponta competência inesperada.")

    release, _ = _json(base_url, "/api/v1/system/release")
    monthly = release.get("monthly")
    rais = release.get("rais")
    if not isinstance(monthly, dict) or not isinstance(rais, dict):
        raise TypeError("Release state sem blocos monthly/rais.")
    if release.get("version") != expected_version:
        raise RuntimeError("Release state expõe versão divergente.")
    if monthly.get("latest_competence") != expected_monthly:
        raise RuntimeError("Release state expõe competência mensal divergente.")
    if monthly.get("policy_max_competence") != expected_monthly:
        raise RuntimeError("Cobertura em produção diverge da política esperada.")
    if int(rais.get("latest_published_year") or 0) != expected_rais_year:
        raise RuntimeError("Release state expõe RAIS divergente.")

    overview, _ = _json(base_url, "/api/v1/indicators/overview")
    if overview.get("competence") != expected_monthly:
        raise RuntimeError("Overview mensal está em competência divergente.")
    admissions = int(overview.get("admissions") or 0)
    dismissals = int(overview.get("dismissals") or 0)
    balance = int(overview.get("balance") or 0)
    if admissions - dismissals != balance:
        raise RuntimeError("Overview mensal falhou na identidade do saldo.")

    rais_overview, _ = _json(base_url, "/api/v1/rais/overview")
    if int(rais_overview.get("year") or 0) != expected_rais_year:
        raise RuntimeError("Overview RAIS está em ano divergente.")
    if int(rais_overview.get("active_stock_tech") or 0) <= 0:
        raise RuntimeError("Overview RAIS não expõe estoque tech válido.")

    docs_status, _, docs_body = _request(base_url, "/docs")
    if docs_status != 200 or b"Swagger UI" not in docs_body:
        raise RuntimeError("Swagger/OpenAPI não está acessível.")

    root_status, _, root_body = _request(base_url, "/")
    if root_status != 200 or b"Mercado Tech Brasil" not in root_body:
        raise RuntimeError("Frontend público não está acessível.")

    return {
        "status": "ok",
        "version": expected_version,
        "monthly": expected_monthly,
        "rais_year": expected_rais_year,
        "admissions": admissions,
        "dismissals": dismissals,
        "balance": balance,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke test do Mercado Tech Brasil em produção."
    )
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--expected-monthly", required=True)
    parser.add_argument("--expected-rais-year", required=True, type=int)
    parser.add_argument("--attempts", type=int, default=20)
    parser.add_argument("--delay-seconds", type=int, default=15)
    args = parser.parse_args()

    if args.attempts < 1:
        raise SystemExit("--attempts precisa ser maior que zero.")

    last_error: Exception | None = None
    for attempt in range(1, args.attempts + 1):
        try:
            result = validate(
                base_url=args.base_url,
                expected_version=args.expected_version,
                expected_monthly=args.expected_monthly,
                expected_rais_year=args.expected_rais_year,
            )
        except (AssertionError, HTTPError, URLError, OSError, ValueError, TypeError, RuntimeError) as exc:
            last_error = exc
            print(
                f"attempt={attempt}/{args.attempts} status=retry "
                f"error={exc}"
            )
            if attempt < args.attempts:
                time.sleep(args.delay_seconds)
            continue

        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return

    raise SystemExit(f"Production smoke failed: {last_error}")


if __name__ == "__main__":
    main()
