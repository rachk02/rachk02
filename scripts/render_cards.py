"""Dessine les cartes SVG du profil depuis data/contributions.json.

Usage :
  python scripts/render_cards.py          # cartes animees
  STATIC=1 python scripts/render_cards.py # image finale, sans animation
"""

from __future__ import annotations

import base64
import datetime as dt
import json
import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from config import COLORS, PERSON, TILES  # noqa: E402

STATIC = os.environ.get("STATIC") == "1"
CARDS = Path(os.environ.get("CARDS_DIR", ROOT / "cards"))
FONTS = ROOT / "fonts"

FONT_FILES = {
    ("Instrument Serif", 400): "InstrumentSerif-Regular.woff2",
    ("Space Grotesk", 400): "SpaceGrotesk-400.woff2",
    ("Space Grotesk", 500): "SpaceGrotesk-500.woff2",
    ("Space Grotesk", 700): "SpaceGrotesk-700.woff2",
    ("JetBrains Mono", 400): "JetBrainsMono-400.woff2",
    ("JetBrains Mono", 700): "JetBrainsMono-700.woff2",
}

C = COLORS


def font_css(families: list[str]) -> str:
    rules = []
    for (family, weight), filename in FONT_FILES.items():
        if family not in families:
            continue
        raw = (FONTS / filename).read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        rules.append(
            "@font-face{font-family:'%s';font-weight:%d;font-style:normal;"
            "src:url(data:font/woff2;base64,%s) format('woff2')}"
            % (family, weight, b64)
        )
    return "".join(rules)


BASE_CSS = f"""
text{{font-kerning:normal;text-rendering:geometricPrecision}}
.mono{{font-family:'JetBrains Mono',monospace}}
.grot{{font-family:'Space Grotesk',sans-serif}}
.serif{{font-family:'Instrument Serif',serif}}
.anim{{animation-duration:.9s;animation-fill-mode:both;animation-timing-function:cubic-bezier(.2,.9,.2,1)}}
.rise{{animation-name:rise}}
.fade{{animation-name:fade}}
.growx{{animation-name:growx;transform-box:fill-box;transform-origin:left center}}
.growy{{animation-name:growy;transform-box:fill-box;transform-origin:50% 100%}}
.swing{{animation-name:swing;transform-box:fill-box;transform-origin:50% 90%;animation-duration:1.1s}}
.pulse{{animation:pulse 2.6s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
.nudge{{animation:nudge 2.6s ease-in-out infinite}}
.shine{{animation:shine 7.5s cubic-bezier(.4,0,.2,1) infinite}}
.sweep{{animation:sweep 8s cubic-bezier(.4,0,.2,1) infinite}}
@keyframes rise{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes growx{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes growy{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
@keyframes pulse{{0%,100%{{opacity:.3;transform:scale(.75)}}50%{{opacity:1;transform:scale(1)}}}}
@keyframes nudge{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(3px,-3px)}}}}
@keyframes swing{{0%{{opacity:0;transform:translateY(34px) rotate(-4deg)}}55%{{opacity:1;transform:translateY(-6px) rotate(1.1deg)}}78%{{transform:translateY(3px) rotate(-.5deg)}}100%{{opacity:1;transform:translateY(0) rotate(0)}}}}
@keyframes shine{{0%,58%{{transform:translateX(0)}}72%,100%{{transform:translateX(1150px)}}}}
@keyframes sweep{{0%,55%{{transform:translateX(0)}}75%,100%{{transform:translateX(420px)}}}}
@media (prefers-reduced-motion: reduce){{.anim,.pulse,.nudge,.shine,.sweep{{animation:none!important;opacity:1!important;transform:none!important}}}}
"""


def svg_open(width: int, height: int, label: str, families: list[str], extra: str = "") -> str:
    style = font_css(families) + BASE_CSS
    if STATIC:
        style += "*{animation:none!important}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">\n'
        f"<style>{style}{extra}</style>\n"
    )


def write(name: str, body: str) -> None:
    CARDS.mkdir(parents=True, exist_ok=True)
    (CARDS / name).write_text(body, encoding="utf-8")
    print(f"cards/{name}")


def load_data() -> dict:
    path = ROOT / "data" / "contributions.json"
    if not path.exists():
        raise SystemExit("data/contributions.json absent : lance fetch_contributions.py d'abord.")
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- hero


RF = {
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
}


def hero(data: dict) -> str:
    w, h = 880, 300
    panel_x, panel_y, panel_w, panel_h = 576, 40, 272, 220
    step = 17
    cols = 11
    rows = 7
    grid_w = (cols - 1) * step + 11
    grid_h = (rows - 1) * step + 11
    gx = panel_x + (panel_w - grid_w) / 2 + 5.5
    gy = 92

    dots = []
    for r in range(rows):
        for col in range(cols):
            letter = 0 if col < 5 else 1
            bit_col = col if col < 5 else col - 6
            glyph = RF["R" if letter == 0 else "F"]
            on = glyph[r][bit_col] == "1"
            cx = gx + col * step
            cy = gy + r * step
            delay = 0.45 + r * 0.075 + col * 0.012
            if on:
                fill = C["blue"] if letter == 0 else C["ink"]
                radius = 5.2
            else:
                fill = C["dot"]
                radius = 1.3
            dots.append(
                f'<circle class="anim fade" style="animation-delay:{delay:.3f}s" '
                f'cx="{cx:.1f}" cy="{cy:.1f}" r="{radius}" fill="{fill}"/>'
            )

    extra = f"""
    .name{{font-family:'Instrument Serif',serif;font-size:72px;fill:{C['ink']}}}
    .maskName{{font-family:'Instrument Serif',serif;font-size:72px;fill:#fff}}
    .eyebrow{{font-size:9.5px;letter-spacing:2.4px;fill:{C['ink_soft']}}}
    .tagline{{font-family:'Space Grotesk',sans-serif;font-size:14.5px;font-weight:500;fill:{C['ink_soft']}}}
    .stack{{font-size:9px;letter-spacing:1.5px;fill:{C['muted']}}}
    """
    out = [svg_open(w, h, f"{PERSON['first']} {PERSON['last']}, {PERSON['role']}", ["Instrument Serif", "Space Grotesk", "JetBrains Mono"], extra)]
    out.append(
        f'<defs><pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">'
        f'<circle cx="1.2" cy="1.2" r="1" fill="#E8DFCE"/></pattern>'
        f'<mask id="lastMask" maskUnits="userSpaceOnUse" x="0" y="0" width="{w}" height="{h}">'
        f'<text class="maskName" x="32" y="198">{escape(PERSON["last"])}</text></mask></defs>'
    )
    out.append(f'<rect width="{w}" height="{h}" fill="{C["paper"]}"/>')
    out.append(f'<rect width="{w}" height="{h}" fill="url(#dots)" opacity=".6"/>')

    out.append(
        f'<text class="mono eyebrow anim fade" style="animation-delay:.1s" x="32" y="52">'
        f'{escape(PERSON["role"].upper())} / {escape(PERSON["location"].upper())}</text>'
    )
    out.append(
        f'<text class="name anim rise" style="animation-delay:.22s" x="30" y="130">'
        f'{escape(PERSON["first"])}</text>'
    )
    out.append(
        f'<text class="name anim rise" style="animation-delay:.38s" x="30" y="200">'
        f'{escape(PERSON["last"])}</text>'
    )
    out.append(
        f'<rect class="anim shine" x="-200" y="146" width="88" height="66" '
        f'fill="{C["blue"]}" mask="url(#lastMask)" style="animation-delay:1.6s"/>'
    )
    out.append(
        f'<rect class="anim growx" style="animation-delay:.7s" x="32" y="222" width="268" height="2" fill="{C["blue"]}"/>'
    )
    out.append(
        f'<text class="tagline anim rise" style="animation-delay:.85s" x="32" y="250">'
        f'{escape(PERSON["tagline"])}</text>'
    )
    out.append(
        f'<text class="mono stack anim fade" style="animation-delay:1s" x="32" y="274">'
        f'{escape(PERSON["stack"])}</text>'
    )

    out.append(
        f'<rect class="anim fade" style="animation-delay:.05s" x="{panel_x}" y="{panel_y}" '
        f'width="{panel_w}" height="{panel_h}" rx="4" fill="{C["panel"]}" stroke="{C["line"]}"/>'
    )
    out.append(
        f'<text class="mono anim fade" style="animation-delay:.2s;font-size:9px;letter-spacing:2.2px;fill:{C["muted"]}" '
        f'x="{panel_x + 20}" y="{panel_y + 26}">SIGNAL / {dt.date.today().year}</text>'
    )
    out.extend(dots)
    out.append(
        f'<circle class="pulse" cx="{panel_x + 26}" cy="{panel_y + 192}" r="3.2" fill="{C["blue"]}"/>'
    )
    out.append(
        f'<text class="mono anim fade" style="animation-delay:1.2s;font-size:8.5px;letter-spacing:1.6px;fill:{C["ink_soft"]}" '
        f'x="{panel_x + 36}" y="{panel_y + 195}">{escape(PERSON["status"].upper())}</text>'
    )
    out.append(
        f'<text class="mono anim fade" style="animation-delay:1.3s;font-size:8.5px;letter-spacing:1.6px;fill:{C["muted"]}" '
        f'x="{panel_x + panel_w - 20}" y="{panel_y + 195}" text-anchor="end">DEPUIS {PERSON["since"]}</text>'
    )
    out.append("</svg>")
    return "\n".join(out)


# -------------------------------------------------------------------------- graph


def level(count: int, top: int) -> int:
    if count <= 0:
        return 0
    if top <= 1:
        return 4
    ratio = count / top
    if ratio > 0.65:
        return 4
    if ratio > 0.4:
        return 3
    if ratio > 0.2:
        return 2
    return 1


GRAPH_FILLS = ["#E8E0CF", C["blue_soft"], "#9AACF8", "#6279F4", C["blue"]]


def graph(data: dict) -> str:
    w, h = 880, 190
    weeks = data["weeks"]
    step, cell = 14, 12
    x0, y0 = 40, 62
    top = max((day["count"] for week in weeks for day in week), default=1)

    extra = f"""
    .label{{font-size:10px;letter-spacing:2.2px;fill:{C['ink']}}}
    .meta{{font-size:9px;letter-spacing:1.6px;fill:{C['muted']}}}
    .month{{font-size:9px;letter-spacing:.6px;fill:{C['muted']}}}
    """
    out = [svg_open(w, h, "Calendrier de mes contributions GitHub", ["Space Grotesk", "JetBrains Mono"], extra)]
    out.append(f'<rect x="0" y="0" width="{w}" height="{h}" rx="4" fill="{C["panel"]}" stroke="{C["line"]}"/>')
    out.append(
        f'<text class="mono label anim fade" style="animation-delay:.05s" x="32" y="34">CONTRIBUTIONS</text>'
    )
    out.append(
        f'<text class="mono meta anim fade" style="animation-delay:.15s" x="{w - 32}" y="34" text-anchor="end">'
        f'{data["total"]} SUR 12 MOIS</text>'
    )

    months = []
    previous = None
    for wi, week in enumerate(weeks):
        if not week:
            continue
        first = dt.date.fromisoformat(week[0]["date"])
        if first.month != previous:
            if not months or wi - months[-1][0] >= 3:
                months.append((wi, first))
            previous = first.month
    for wi, date in months:
        if wi > len(weeks) - 3:
            continue
        out.append(
            f'<text class="mono month anim fade" style="animation-delay:.3s" '
            f'x="{x0 + wi * step}" y="{y0 - 10}">{MONTH_SHORT[date.month - 1]}</text>'
        )

    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            count = day["count"]
            burn = level(count, top)
            delay = 0.1 + wi * 0.012 + di * 0.002
            out.append(
                f'<rect class="anim fade" style="animation-delay:{delay:.3f}s" x="{x0 + wi * step}" '
                f'y="{y0 + di * step}" width="{cell}" height="{cell}" rx="2" fill="{GRAPH_FILLS[burn]}">'
                f'<title>{day["date"]} : {count} contribution{"s" if count > 1 else ""}</title></rect>'
            )

    legend_x = w - 32
    legend_y = h - 20
    out.append(
        f'<text class="mono meta" x="{legend_x - 104}" y="{legend_y + 8}" text-anchor="end">MOINS</text>'
    )
    for i in range(4):
        out.append(
            f'<rect x="{legend_x - 94 + i * 14}" y="{legend_y}" width="11" height="11" rx="2" fill="{GRAPH_FILLS[i + 1]}"/>'
        )
    out.append(
        f'<text class="mono meta" x="{legend_x + 2}" y="{legend_y + 8}" text-anchor="end">PLUS</text>'
    )
    out.append("</svg>")
    return "\n".join(out)


MONTH_SHORT = ["JAN", "FEV", "MAR", "AVR", "MAI", "JUIN", "JUIL", "AOU", "SEP", "OCT", "NOV", "DEC"]


# ----------------------------------------------------------------------- activity


def activity(data: dict) -> str:
    w, h = 880, 220
    months = data["months"]
    base_y = 176
    max_total = max((m["total"] for m in months), default=1) or 1
    best = max(months, key=lambda m: m["total"]) if months else None
    slot = 49
    bar_w = 27
    x0 = 32

    extra = f"""
    .label{{font-size:10px;letter-spacing:2.2px;fill:{C['ink']}}}
    .meta{{font-size:9px;letter-spacing:1.6px;fill:{C['muted']}}}
    .value{{font-family:'JetBrains Mono',monospace;font-size:9px;fill:{C['ink_soft']}}}
    .month{{font-size:8.5px;letter-spacing:.4px;fill:{C['muted']}}}
    .statLabel{{font-size:8.5px;letter-spacing:1.4px;fill:{C['muted']}}}
    .statValue{{font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:700;fill:{C['ink']}}}
    """
    out = [svg_open(w, h, "Contributions par mois, serie et jours actifs", ["Space Grotesk", "JetBrains Mono"], extra)]
    out.append(f'<rect x="0" y="0" width="{w}" height="{h}" rx="4" fill="{C["panel"]}" stroke="{C["line"]}"/>')
    out.append(f'<text class="mono label anim fade" style="animation-delay:.05s" x="32" y="34">RYTHME</text>')
    out.append(
        f'<text class="mono meta anim fade" style="animation-delay:.15s" x="620" y="34" text-anchor="end">DOUZE DERNIERS MOIS</text>'
    )

    for i, month in enumerate(months):
        height = max(2.0, month["total"] / max_total * 104)
        x = x0 + i * slot + (slot - bar_w) / 2
        y = base_y - height
        colour = C["blue"] if best is not None and month["key"] == best["key"] else C["ink"]
        delay = 0.25 + i * 0.05
        out.append(
            f'<rect class="anim growy" style="animation-delay:{delay:.2f}s" x="{x:.1f}" y="{y:.1f}" '
            f'width="{bar_w}" height="{height:.1f}" rx="2" fill="{colour}">'
            f'<title>{month["label"]} {month["year"]} : {month["total"]} contributions</title></rect>'
        )
        out.append(
            f'<text class="value anim fade" style="animation-delay:{delay + 0.55:.2f}s" '
            f'x="{x + bar_w / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle">{month["total"]}</text>'
        )
        out.append(
            f'<text class="mono month anim fade" style="animation-delay:{delay:.2f}s" '
            f'x="{x + bar_w / 2:.1f}" y="{base_y + 18}">{month["label"]}</text>'
        )

    out.append(f'<line x1="640" y1="58" x2="640" y2="190" stroke="{C["line"]}"/>')

    busiest = dt.date.fromisoformat(data["busiest_day"])
    stats = [
        ("SÉRIE EN COURS", f'{data["current_streak"]} j'),
        ("RECORD", f'{data["longest_streak"]} j'),
        ("JOURS ACTIFS", f'{data["active_days"]}'),
        ("PIC", f'{data["busiest_count"]} / {busiest.day} {MONTH_SHORT[busiest.month - 1]}'),
    ]
    for i, (label, value) in enumerate(stats):
        y = 72 + i * 34
        out.append(
            f'<text class="mono statLabel anim fade" style="animation-delay:{0.5 + i * 0.1:.2f}s" '
            f'x="660" y="{y}">{label}</text>'
        )
        out.append(
            f'<text class="statValue anim fade" style="animation-delay:{0.6 + i * 0.1:.2f}s" '
            f'x="848" y="{y}" text-anchor="end">{escape(value)}</text>'
        )
        if i < len(stats) - 1:
            out.append(f'<line x1="660" y1="{y + 12}" x2="848" y2="{y + 12}" stroke="{C["line"]}" opacity=".7"/>')

    out.append("</svg>")
    return "\n".join(out)


# -------------------------------------------------------------------------- tiles


def wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def tile(item: dict, index: int) -> str:
    w, h = 280, 196
    accent = C[item["color"]]
    description = wrap(item["desc"], 34)
    label_w = len(item["label"]) * 5.9 + (len(item["label"]) - 1) * 2

    extra = f"""
    .index{{font-size:10px;letter-spacing:1.4px;fill:{C['muted']}}}
    .label{{font-size:9.5px;letter-spacing:2px;fill:{accent}}}
    .title{{font-family:'Space Grotesk',sans-serif;font-size:25px;font-weight:700;fill:{C['ink']}}}
    .desc{{font-family:'Space Grotesk',sans-serif;font-size:12px;fill:{C['ink_soft']}}}
    .meta{{font-size:8.5px;letter-spacing:1.2px;fill:{C['muted']}}}
    .arrow{{font-size:14px;fill:{accent}}}
    """
    out = [svg_open(w, h, f"{item['title']} : {item['desc']}", ["Space Grotesk", "JetBrains Mono"], extra)]
    out.append(
        f'<defs><clipPath id="clip"><rect x="0" y="0" width="{w}" height="{h}" rx="4"/></clipPath></defs>'
    )
    out.append(f'<rect x="0" y="0" width="{w}" height="{h}" rx="4" fill="{C["panel"]}" stroke="{C["line"]}"/>')
    out.append(
        f'<rect class="anim fade" style="animation-delay:.05s" x="20" y="0" width="44" height="3" fill="{accent}"/>'
    )
    out.append(f'<g clip-path="url(#clip)">')
    out.append(
        f'<rect class="anim sweep" style="animation-delay:{2 + index * 0.5:.1f}s" x="-90" y="0" '
        f'width="54" height="{h}" fill="{accent}" opacity=".08"/>'
    )
    out.append("</g>")

    out.append(f'<g class="anim swing" style="animation-delay:{0.15 + index * 0.18:.2f}s">')
    out.append(f'<text class="mono index" x="20" y="34">{item["index"]}</text>')
    out.append(
        f'<rect x="{260 - label_w - 12:.1f}" y="25" width="6" height="6" fill="{accent}"/>'
    )
    out.append(
        f'<text class="mono label" x="260" y="34" text-anchor="end">{item["label"]}</text>'
    )
    title_y = 78
    out.append(f'<text class="title" x="20" y="{title_y}">{escape(item["title"])}</text>')
    for i, line in enumerate(description[:2]):
        out.append(f'<text class="desc" x="20" y="{title_y + 26 + i * 17}">{escape(line)}</text>')
    out.append(f'<line x1="20" y1="152" x2="260" y2="152" stroke="{C["line"]}"/>')
    out.append(f'<text class="mono meta" x="20" y="174">{escape(item["meta"])}</text>')
    out.append(f'<text class="mono arrow nudge" x="260" y="175" text-anchor="end">&#8599;</text>')
    out.append("</g>")
    out.append("</svg>")
    return "\n".join(out)


# ------------------------------------------------------------------------- build


def main() -> None:
    data = load_data()
    write("hero.svg", hero(data))
    write("graph.svg", graph(data))
    write("activity.svg", activity(data))
    for i, item in enumerate(TILES):
        write(f"tile-{item['label'].lower()}.svg", tile(item, i))


if __name__ == "__main__":
    main()

