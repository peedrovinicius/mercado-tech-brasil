from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "gold"
DEFAULT_OUTPUT = ROOT / "assets" / "readme-dashboard.svg"

NORTHEAST_UFS = {"AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"}
MONTHS = {
    "01": "Jan",
    "02": "Fev",
    "03": "Mar",
    "04": "Abr",
    "05": "Mai",
    "06": "Jun",
    "07": "Jul",
    "09": "Set",
    "10": "Out",
    "11": "Nov",
    "12": "Dez",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def format_int(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def format_percent(value: float) -> str:
    return f"{value * 100:.2f}%".replace(".", ",")


def competence_label(value: str) -> str:
    return f"{MONTHS[value[4:6]]}/{value[:4]}"


def chart_points(
    values: list[int],
    *,
    left: float = 90,
    right: float = 790,
    top: float = 420,
    bottom: float = 590,
    lower: int,
    upper: int,
) -> str:
    if len(values) == 1:
        xs = [left]
    else:
        step = (right - left) / (len(values) - 1)
        xs = [left + step * index for index in range(len(values))]

    span = max(upper - lower, 1)
    points = []
    for x, value in zip(xs, values, strict=True):
        y = bottom - ((value - lower) / span) * (bottom - top)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def circle_nodes(points: str, color: str) -> str:
    nodes = []
    for point in points.split():
        x, y = point.split(",")
        nodes.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>')
    return "".join(nodes)


def build_dashboard() -> str:
    trend = load_json(GOLD / "trend.json")
    items = sorted(trend["items"], key=lambda item: item["competence"])
    latest = items[-1]
    competence = latest["competence"]

    overview = load_json(GOLD / f"overview-{competence}.json")
    by_uf = load_json(GOLD / f"by-uf-{competence}.json")

    admissions_total = sum(item["admissions"] for item in items)
    dismissals_total = sum(item["dismissals"] for item in items)
    balance_total = sum(item["balance"] for item in items)

    uf_items = by_uf["items"]
    brazil_admissions = sum(item["admissions"] for item in uf_items)
    northeast_admissions = sum(
        item["admissions"] for item in uf_items if item["uf"] in NORTHEAST_UFS
    )
    ceara_admissions = next(
        item["admissions"] for item in uf_items if item["uf"] == "CE"
    )

    northeast_share = northeast_admissions / brazil_admissions
    ceara_brazil_share = ceara_admissions / brazil_admissions
    ceara_northeast_share = ceara_admissions / northeast_admissions

    admissions = [item["admissions"] for item in items]
    dismissals = [item["dismissals"] for item in items]
    lower = min(admissions + dismissals)
    upper = max(admissions + dismissals)

    admissions_points = chart_points(
        admissions,
        lower=lower,
        upper=upper,
    )
    dismissals_points = chart_points(
        dismissals,
        lower=lower,
        upper=upper,
    )

    labels = []
    if len(items) == 1:
        xs = [90.0]
    else:
        step = 700 / (len(items) - 1)
        xs = [90 + step * index for index in range(len(items))]
    for x, item in zip(xs, items, strict=True):
        month = competence_label(item["competence"]).split("/")[0]
        labels.append(
            f'<text x="{x:.1f}" y="618" '
            'font-family="Inter,Arial,sans-serif" font-size="11" '
            f'fill="#77777f" text-anchor="middle">{month}</text>'
        )

    northeast_bar = 216 * northeast_share
    ceara_brazil_bar = 216 * ceara_brazil_share
    ceara_northeast_bar = 216 * ceara_northeast_share

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760"
  viewBox="0 0 1200 760" role="img" aria-labelledby="title desc">
  <title id="title">Dashboard executivo do Mercado Tech Brasil</title>
  <desc id="desc">Resumo visual da série publicada com indicadores acumulados,
  evolução mensal e comparação territorial.</desc>
  <rect width="1200" height="760" rx="28" fill="#f7f7f9"/>
  <rect x="24" y="24" width="1152" height="712" rx="24"
    fill="#ffffff" stroke="#dedee4"/>

  <text x="60" y="78" font-family="Inter,Arial,sans-serif" font-size="16"
    font-weight="700" fill="#6f6f77" letter-spacing="1.8">MERCADO TECH BRASIL</text>
  <text x="60" y="120" font-family="Inter,Arial,sans-serif" font-size="34"
    font-weight="800" fill="#171719">Dashboard executivo</text>
  <text x="60" y="150" font-family="Inter,Arial,sans-serif" font-size="15"
    fill="#707078">Série publicada: {competence_label(items[0]["competence"])} a
    {competence_label(competence)}</text>
  <rect x="930" y="70" width="186" height="34" rx="17"
    fill="#edf1ff" stroke="#d5deff"/>
  <circle cx="953" cy="87" r="5" fill="#2f63ff"/>
  <text x="968" y="92" font-family="Inter,Arial,sans-serif" font-size="13"
    font-weight="700" fill="#2459ff">Dados publicados</text>

  <g font-family="Inter,Arial,sans-serif">
    <rect x="60" y="190" width="250" height="108" rx="16" fill="#171719"/>
    <text x="82" y="220" font-size="12" font-weight="700" fill="#a9a9b1"
      letter-spacing="1">ADMISSÕES TECH</text>
    <text x="82" y="264" font-size="34" font-weight="800"
      fill="#ffffff">{format_int(admissions_total)}</text>
    <text x="82" y="284" font-size="11" fill="#a9a9b1">acumulado da série</text>

    <rect x="330" y="190" width="250" height="108" rx="16"
      fill="#f5f5f7" stroke="#e0e0e5"/>
    <text x="352" y="220" font-size="12" font-weight="700" fill="#7a7a82"
      letter-spacing="1">DESLIGAMENTOS</text>
    <text x="352" y="264" font-size="34" font-weight="800"
      fill="#171719">{format_int(dismissals_total)}</text>
    <text x="352" y="284" font-size="11" fill="#888890">acumulado da série</text>

    <rect x="600" y="190" width="250" height="108" rx="16"
      fill="#f5f5f7" stroke="#e0e0e5"/>
    <text x="622" y="220" font-size="12" font-weight="700" fill="#7a7a82"
      letter-spacing="1">SALDO ACUMULADO</text>
    <text x="622" y="264" font-size="34" font-weight="800"
      fill="#17643b">{'+' if balance_total >= 0 else ''}{format_int(balance_total)}</text>
    <text x="622" y="284" font-size="11" fill="#888890">{len(items)} competências</text>

    <rect x="870" y="190" width="246" height="108" rx="16"
      fill="#edf1ff" stroke="#d7e0ff"/>
    <text x="892" y="220" font-size="12" font-weight="700" fill="#5e6f9b"
      letter-spacing="1">{competence_label(competence).upper()}</text>
    <text x="892" y="264" font-size="34" font-weight="800"
      fill="#2459ff">{'+' if overview["balance"] >= 0 else ''}{format_int(overview["balance"])}</text>
    <text x="892" y="284" font-size="11" fill="#68769b">saldo da competência</text>
  </g>

  <text x="60" y="346" font-family="Inter,Arial,sans-serif" font-size="13"
    font-weight="700" fill="#6f6f77" letter-spacing="1">EVOLUÇÃO MENSAL</text>
  <text x="60" y="372" font-family="Inter,Arial,sans-serif" font-size="23"
    font-weight="800" fill="#171719">Admissões e desligamentos tech</text>

  <line x1="90" y1="420" x2="790" y2="420" stroke="#eeeef2"/>
  <line x1="90" y1="465" x2="790" y2="465" stroke="#eeeef2"/>
  <line x1="90" y1="510" x2="790" y2="510" stroke="#eeeef2"/>
  <line x1="90" y1="555" x2="790" y2="555" stroke="#eeeef2"/>

  <polyline points="{admissions_points}" fill="none" stroke="#171719"
    stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="{dismissals_points}" fill="none" stroke="#2459ff"
    stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
  <g>{circle_nodes(admissions_points, "#171719")}</g>
  <g>{circle_nodes(dismissals_points, "#2459ff")}</g>
  <g>{"".join(labels)}</g>

  <circle cx="90" cy="647" r="5" fill="#171719"/>
  <text x="104" y="652" font-family="Inter,Arial,sans-serif" font-size="12"
    fill="#55555c">Admissões</text>
  <circle cx="187" cy="647" r="5" fill="#2459ff"/>
  <text x="201" y="652" font-family="Inter,Arial,sans-serif" font-size="12"
    fill="#55555c">Desligamentos</text>

  <rect x="840" y="350" width="276" height="318" rx="18"
    fill="#f7f7f9" stroke="#e1e1e5"/>
  <text x="866" y="386" font-family="Inter,Arial,sans-serif" font-size="12"
    font-weight="700" fill="#77777f" letter-spacing="1">RECORTE TERRITORIAL</text>
  <text x="866" y="418" font-family="Inter,Arial,sans-serif" font-size="21"
    font-weight="800" fill="#171719">{competence_label(competence)}</text>

  <text x="866" y="468" font-family="Inter,Arial,sans-serif" font-size="13"
    fill="#55555c">Nordeste / Brasil</text>
  <text x="1082" y="468" text-anchor="end" font-family="Inter,Arial,sans-serif"
    font-size="18" font-weight="800" fill="#171719">{format_percent(northeast_share)}</text>
  <rect x="866" y="482" width="216" height="9" rx="4.5" fill="#e3e3e8"/>
  <rect x="866" y="482" width="{northeast_bar:.1f}" height="9" rx="4.5"
    fill="#171719"/>

  <text x="866" y="534" font-family="Inter,Arial,sans-serif" font-size="13"
    fill="#55555c">Ceará / Brasil</text>
  <text x="1082" y="534" text-anchor="end" font-family="Inter,Arial,sans-serif"
    font-size="18" font-weight="800" fill="#2459ff">{format_percent(ceara_brazil_share)}</text>
  <rect x="866" y="548" width="216" height="9" rx="4.5" fill="#e3e3e8"/>
  <rect x="866" y="548" width="{ceara_brazil_bar:.1f}" height="9" rx="4.5"
    fill="#2459ff"/>

  <text x="866" y="600" font-family="Inter,Arial,sans-serif" font-size="13"
    fill="#55555c">Ceará / Nordeste</text>
  <text x="1082" y="600" text-anchor="end" font-family="Inter,Arial,sans-serif"
    font-size="18" font-weight="800" fill="#17643b">{format_percent(ceara_northeast_share)}</text>
  <rect x="866" y="614" width="216" height="9" rx="4.5" fill="#e3e3e8"/>
  <rect x="866" y="614" width="{ceara_northeast_bar:.1f}" height="9" rx="4.5"
    fill="#17643b"/>

  <text x="60" y="704" font-family="Inter,Arial,sans-serif" font-size="11"
    fill="#85858d">Fonte: Novo CAGED / MTE. Recorte ocupacional CBO v2.
    Valores publicados no repositório.</text>
</svg>
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera o dashboard visual do README a partir dos artefatos Gold."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Arquivo SVG de saída.",
    )
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_dashboard(), encoding="utf-8")


if __name__ == "__main__":
    main()
