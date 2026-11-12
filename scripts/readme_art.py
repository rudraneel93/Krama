"""Generate the animated SVG artwork used by README.md (light and dark variants).

GitHub renders SVGs referenced with <img> and runs their CSS animations, but it cannot load
web fonts inside them, so brand text (the Syne wordmark, Sora headlines) is converted to
vector outlines with fontTools. Body text uses the system font stack.

    uv venv /tmp/fontenv && uv pip install --python /tmp/fontenv/bin/python fonttools
    /tmp/fontenv/bin/python scripts/readme_art.py --fonts <dir with Syne.ttf and Sora.ttf>

Writes docs/readme/*.svg.
"""
import argparse
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

OUT = Path(__file__).resolve().parent.parent / "docs" / "readme"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

PAL = {
    "dark": {"bg": "#05060a", "bg2": "#0c0f18", "panel": "#111522", "line": "#232a3b", "fg": "#f2f5fa",
             "muted": "#a1abbc", "dim": "#5f6a7d", "rule": "#2ef2c8", "sky": "#5aa9ff", "violet": "#8b7cff",
             "brk": "#ff9f1c", "glow": "0.35"},
    "light": {"bg": "#ffffff", "bg2": "#f5f7fb", "panel": "#ffffff", "line": "#e2e7f0", "fg": "#0a1020",
              "muted": "#4b586c", "dim": "#8a96a8", "rule": "#00a57f", "sky": "#2563eb", "violet": "#6a4cff",
              "brk": "#e07800", "glow": "0.18"},
}


class Outliner:
    def __init__(self, path: Path, weight: int):
        self.font = instantiateVariableFont(TTFont(str(path)), {"wght": weight})
        self.gs, self.cmap = self.font.getGlyphSet(), self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm

    def path(self, text: str, size: float, x: float, y: float, tracking: float = 0.0) -> tuple[str, float]:
        s, cx, parts = size / self.upm, x, []
        for ch in text:
            g = self.cmap.get(ord(ch))
            if g is None:
                cx += size * 0.3
                continue
            pen = SVGPathPen(self.gs, ntos=lambda v: f"{v:.1f}")
            self.gs[g].draw(TransformPen(pen, (s, 0, 0, -s, cx, y)))
            parts.append(pen.getCommands())
            cx += self.gs[g].width * s + tracking * size
        return " ".join(parts), cx - x


def mark(x: float, y: float, size: float) -> str:
    """The Krama mark (abstract K: rule, ghost leg, slipped value) at (x, y)."""
    k = size / 64
    return f'''<g transform="translate({x},{y}) scale({k})">
  <rect width="64" height="64" rx="17" fill="url(#kbg)"/>
  <rect x=".75" y=".75" width="62.5" height="62.5" rx="16.4" fill="none" stroke="#fff" stroke-opacity=".08" stroke-width="1.5"/>
  <rect x="15" y="13" width="7.5" height="38" rx="3.75" fill="url(#krule)"/>
  <path d="M25 34.5 L46.5 13" stroke="url(#krule)" stroke-width="7.5" stroke-linecap="round"/>
  <path d="M30.5 30.5 L41 41" stroke="#9fb4ff" stroke-opacity=".25" stroke-width="7.5" stroke-linecap="round"/>
  <circle cx="45.5" cy="48" r="6.2" fill="url(#kbrk)"/>
</g>'''


DEFS = '''<defs>
  <linearGradient id="kbg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#16203a"/><stop offset="1" stop-color="#05070d"/></linearGradient>
  <linearGradient id="krule" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#2ef2c8"/><stop offset=".55" stop-color="#4fb3ff"/><stop offset="1" stop-color="#9b84ff"/></linearGradient>
  <radialGradient id="kbrk" cx=".38" cy=".35" r=".75"><stop offset="0" stop-color="#ffd27a"/><stop offset=".55" stop-color="#ff9f1c"/><stop offset="1" stop-color="#ff6a00"/></radialGradient>
  <linearGradient id="grad" x1="0" x2="1"><stop offset="0" stop-color="#2ef2c8"/><stop offset=".5" stop-color="#5aa9ff"/><stop offset="1" stop-color="#8b7cff"/></linearGradient>
  <radialGradient id="halo" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#2ef2c8" stop-opacity="{glow}"/><stop offset="1" stop-color="#2ef2c8" stop-opacity="0"/></radialGradient>
  <radialGradient id="halo2" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#8b7cff" stop-opacity="{glow}"/><stop offset="1" stop-color="#8b7cff" stop-opacity="0"/></radialGradient>
</defs>'''


def svg(w: int, h: int, body: str, css: str, p: dict) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'font-family="{SANS}">\n<style>{css}\n@media (prefers-reduced-motion: reduce) '
            '{ * { animation: none !important; } .rv { opacity: 1 !important; } }</style>\n'
            + DEFS.replace("{glow}", p["glow"]) + "\n" + body + "\n</svg>\n")


# --------------------------------------------------------------------------------------------
def banner(theme: str, syne: Outliner, sora: Outliner) -> str:
    p = PAL[theme]
    W, H, C = 1280, 440, 10  # C = animation cycle seconds
    word, ww = syne.path("krama", 66, 152, 128, tracking=-0.01)
    h1, _ = sora.path("Every number,", 54, 64, 236, tracking=-0.035)
    h2, _ = sora.path("in its place.", 54, 64, 300, tracking=-0.035)
    # the animated chart
    X0, X1, Y0, Y1, n, brk = 720, 1200, 360, 110, 12, 7
    vals = [5011 + i for i in range(n)]
    actual = [v + (1 if i == brk else 0) for i, v in enumerate(vals)]
    actual[brk] = vals[brk] + 3  # displaced visibly for the drawing
    lo, hi = min(vals) - 1, max(actual) + 1

    def X(i):
        return X0 + i * (X1 - X0) / (n - 1)

    def Y(v):
        return Y0 - (v - lo) * (Y0 - Y1) / (hi - lo)
    rule = "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
    dots = "\n".join(
        f'<circle class="d" style="animation-delay:{i * 0.09:.2f}s" cx="{X(i):.1f}" cy="{Y(v):.1f}" r="7" fill="{p["sky"]}"/>'
        f'<circle class="ok" cx="{X(i):.1f}" cy="{Y(v):.1f}" r="7" fill="{p["rule"]}"/>'
        for i, v in enumerate(actual) if i != brk)
    bx, by, ey = X(brk), Y(actual[brk]), Y(vals[brk])
    grid = "\n".join(f'<line x1="{X0 - 20}" x2="{X1 + 20}" y1="{y}" y2="{y}" stroke="{p["line"]}"/>' for y in (110, 193, 276, 360))
    css = f'''
.d {{ opacity: 0; animation: pop {C}s infinite; }}
@keyframes pop {{ 0% {{ opacity: 0; transform: translateY(-10px); }} 4% {{ opacity: 1; transform: none; }} 90% {{ opacity: 1; }} 97%, 100% {{ opacity: 0; }} }}
.ok {{ opacity: 0; animation: ok {C}s infinite; }}
@keyframes ok {{ 0%, 33% {{ opacity: 0; }} 37%, 90% {{ opacity: 1; }} 97%, 100% {{ opacity: 0; }} }}
.rl {{ stroke-dasharray: 560; stroke-dashoffset: 560; animation: draw {C}s infinite; }}
@keyframes draw {{ 0%, 14% {{ stroke-dashoffset: 560; }} 32%, 90% {{ stroke-dashoffset: 0; opacity: 1; }} 97%, 100% {{ stroke-dashoffset: 0; opacity: 0; }} }}
.bd {{ opacity: 0; animation: bd {C}s infinite; }}
@keyframes bd {{ 0%, 9% {{ opacity: 0; }} 12%, 90% {{ opacity: 1; }} 97%, 100% {{ opacity: 0; }} }}
.ring {{ opacity: 0; transform-box: fill-box; transform-origin: center; animation: ring {C}s infinite; }}
@keyframes ring {{ 0%, 38% {{ opacity: 0; transform: scale(2.6); }} 44% {{ opacity: 1; transform: scale(1); }} 48% {{ transform: scale(1.18); }} 52%, 90% {{ opacity: 1; transform: scale(1); }} 97%, 100% {{ opacity: 0; }} }}
.ghost, .link {{ opacity: 0; animation: lbl {C}s infinite; }}
.lbl {{ opacity: 0; animation: lbl {C}s infinite; }}
@keyframes lbl {{ 0%, 46% {{ opacity: 0; }} 52%, 90% {{ opacity: 1; }} 97%, 100% {{ opacity: 0; }} }}
.chip {{ animation: chip {C}s infinite; }}
@keyframes chip {{ 0%, 44% {{ opacity: 0; }} 50%, 90% {{ opacity: 1; }} 97%, 100% {{ opacity: 0; }} }}
.scan {{ animation: scan {C}s infinite; }}
@keyframes scan {{ 0%, 12% {{ transform: translateX(-60px); opacity: 0; }} 16% {{ opacity: .9; }} 32% {{ transform: translateX(540px); opacity: .9; }} 34%, 100% {{ transform: translateX(540px); opacity: 0; }} }}
.floaty {{ animation: fl 7s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
@keyframes fl {{ 50% {{ transform: translateY(-6px); }} }}'''
    body = f'''<rect width="{W}" height="{H}" rx="28" fill="{p["bg"]}"/>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="27.5" fill="none" stroke="{p["line"]}"/>
<circle cx="980" cy="200" r="330" fill="url(#halo)"/><circle cx="260" cy="420" r="300" fill="url(#halo2)"/>
<g class="floaty">{mark(64, 70, 72)}</g>
<path d="{word}" fill="{p["fg"]}"/>
<text x="{152 + ww + 16}" y="126" font-family="{MONO}" font-size="13" letter-spacing="2" fill="{p["dim"]}">POWERED BY PIM</text>
<path d="{h1}" fill="{p["fg"]}"/>
<path d="{h2}" fill="url(#grad)"/>
<text x="64" y="350" font-size="19" fill="{p["muted"]}">Finds the rule a column of numbers follows — and shows exactly</text>
<text x="64" y="378" font-size="19" fill="{p["muted"]}">which rows break it, with the value they should have been.</text>
<g>
  <rect x="684" y="64" width="552" height="330" rx="20" fill="{p["bg2"]}" stroke="{p["line"]}"/>
  <circle cx="708" cy="88" r="5" fill="#ff5f57"/><circle cx="726" cy="88" r="5" fill="#febc2e"/><circle cx="744" cy="88" r="5" fill="#28c840"/>
  <text x="764" y="92" font-family="{MONO}" font-size="12" fill="{p["muted"]}">invoices.xlsx · invoice_no</text>
  {grid}
  <rect class="scan" x="700" y="104" width="60" height="262" fill="url(#halo)"/>
  <path class="rl" d="{rule}" fill="none" stroke="url(#grad)" stroke-width="3.5" stroke-linecap="round"/>
  {dots}
  <circle class="bd" cx="{bx:.1f}" cy="{by:.1f}" r="7" fill="{p["brk"]}"/>
  <circle class="ring" cx="{bx:.1f}" cy="{by:.1f}" r="16" fill="none" stroke="{p["brk"]}" stroke-width="2.5"/>
  <line class="link" x1="{bx:.1f}" x2="{bx:.1f}" y1="{ey + 8:.1f}" y2="{by - 16:.1f}" stroke="{p["brk"]}" stroke-width="2" stroke-dasharray="4 4"/>
  <circle class="ghost" cx="{bx:.1f}" cy="{ey:.1f}" r="7" fill="none" stroke="{p["muted"]}" stroke-width="1.6" stroke-dasharray="3 3"/>
  <g class="lbl"><rect x="{bx - 222:.1f}" y="{by - 17:.1f}" width="196" height="34" rx="10" fill="{p["panel"]}" stroke="{p["brk"]}" stroke-opacity=".6"/>
    <text x="{bx - 208:.1f}" y="{by + 5:.1f}" font-family="{MONO}" font-size="13" fill="{p["brk"]}">row 8 → should be 5,018</text></g>
  <g class="chip"><rect x="1050" y="76" width="168" height="26" rx="13" fill="{p["brk"]}" fill-opacity=".14"/>
    <text x="1134" y="94" text-anchor="middle" font-family="{MONO}" font-size="12" fill="{p["brk"]}">1 wrong value</text></g>
  <text x="708" y="384" font-family="{MONO}" font-size="13" fill="{p["muted"]}">rule <tspan fill="{p["rule"]}" class="lbl">each = previous + 1</tspan></text>
</g>'''
    return svg(W, H, body, css, p)


def how(theme: str, sora: Outliner) -> str:
    p = PAL[theme]
    W, H, C = 1280, 360, 9
    cards = []
    titles = ["You give it a column", "It finds the rule", "It shows what's wrong"]
    subs = [["Paste numbers, upload a spreadsheet,", "or select cells in Excel."],
            ["Steps, ratios, curves, cycles, Fibonacci-like…", "tried, then tested on rows it didn't see."],
            ["Every broken row, the value it should be —", "or “no rule”, never a guess."]]
    for k in range(3):
        x = 32 + k * 416
        t, _ = sora.path(titles[k], 25, x + 28, 254, tracking=-0.02)
        cards.append(f'''<g class="rv" style="animation-delay:{k * 0.25}s">
<rect x="{x}" y="24" width="392" height="312" rx="22" fill="{p["bg2"]}" stroke="{p["line"]}"/>
<rect x="{x + 28}" y="50" width="34" height="34" rx="10" fill="url(#grad)"/>
<text x="{x + 45}" y="73" text-anchor="middle" font-size="17" font-weight="700" fill="#04110d">{k + 1}</text>
<path d="{t}" fill="{p["fg"]}"/>
<text x="{x + 28}" y="284" font-size="15" fill="{p["muted"]}">{subs[k][0]}</text>
<text x="{x + 28}" y="306" font-size="15" fill="{p["muted"]}">{subs[k][1]}</text>
</g>''')
    # card 1: tiles hopping
    tiles = "".join(
        f'<g class="hop" style="animation-delay:{i * 0.12:.2f}s"><rect x="{60 + i * 66}" y="120" width="56" height="40" rx="9" '
        f'fill="{p["panel"]}" stroke="{p["line"]}"/><text x="{88 + i * 66}" y="146" text-anchor="middle" font-family="{MONO}" '
        f'font-size="13" fill="{p["fg"]}">{v}</text></g>' for i, v in enumerate([5011, 5012, 5013, 5015, 5016]))
    # card 2: points and rule drawing
    x2 = 448
    pts = [(x2 + 50 + i * 70, 178 - i * 18) for i in range(5)]
    line2 = "M" + " L".join(f"{a},{b}" for a, b in pts)
    dots2 = "".join(f'<circle cx="{a}" cy="{b}" r="6" fill="{p["sky"]}"/>' for a, b in pts)
    # card 3: highlight
    x3 = 864
    css = f'''
.rv {{ animation: rv 1s cubic-bezier(.2,.8,.2,1) both; }}
@keyframes rv {{ from {{ opacity: 0; transform: translateY(14px); }} }}
.hop {{ animation: hop {C / 3:.1f}s ease-in-out infinite; }}
@keyframes hop {{ 0%, 60%, 100% {{ transform: none; }} 30% {{ transform: translateY(-8px); }} }}
.dr {{ stroke-dasharray: 320; animation: dr {C / 3:.1f}s cubic-bezier(.6,0,.2,1) infinite; }}
@keyframes dr {{ 0% {{ stroke-dashoffset: 320; }} 50%, 85% {{ stroke-dashoffset: 0; }} 100% {{ stroke-dashoffset: -320; }} }}
.pulse {{ transform-box: fill-box; transform-origin: center; animation: pl 1.8s ease-in-out infinite; }}
@keyframes pl {{ 50% {{ transform: scale(1.06); }} }}
.blink {{ animation: bl 1.8s ease-in-out infinite; }}
@keyframes bl {{ 50% {{ opacity: .35; }} }}'''
    body = f'''{"".join(cards)}
{tiles}
<path class="dr" d="{line2}" fill="none" stroke="url(#grad)" stroke-width="3" stroke-linecap="round"/>
{dots2}
<text x="{x2 + 190}" y="214" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{p["rule"]}">each = previous + 1</text>
<g><rect x="{x3 + 30}" y="120" width="76" height="40" rx="9" fill="{p["rule"]}" fill-opacity=".14"/>
<text x="{x3 + 68}" y="146" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{p["rule"]}">5013</text>
<g class="pulse"><rect x="{x3 + 116}" y="120" width="76" height="40" rx="9" fill="{p["brk"]}" fill-opacity=".16" stroke="{p["brk"]}" stroke-width="2"/>
<text x="{x3 + 154}" y="146" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{p["brk"]}">5015</text></g>
<text x="{x3 + 210}" y="146" font-size="16" fill="{p["dim"]}">→</text>
<rect x="{x3 + 232}" y="120" width="132" height="40" rx="9" fill="{p["rule"]}" fill-opacity=".14"/>
<text x="{x3 + 298}" y="146" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{p["rule"]}">should be 5014</text>
<text class="blink" x="{x3 + 30}" y="198" font-family="{MONO}" font-size="12" fill="{p["brk"]}">● 1 missing invoice found</text></g>'''
    return svg(W, H, body, css, p)


def before_after(theme: str, sora: Outliner) -> str:
    p = PAL[theme]
    W, H, C = 1280, 470, 8
    fees = [500 + 125 * i for i in range(10)]
    shown = fees[:]
    shown[3], shown[7] = 950, 1400
    t1, _ = sora.path("Your fee table", 22, 64, 64, tracking=-0.02)
    t2, _ = sora.path("After Krama", 22, 684, 64, tracking=-0.02)

    def table(x0, after):
        rows = []
        for i, v in enumerate(shown):
            y = 92 + i * 33
            bad = v != fees[i]
            fill = p["panel"] if i % 2 else p["bg2"]
            if after and bad:
                rows.append(f'<g class="hit" style="animation-delay:{0.45 + i * 0.16:.2f}s"><rect x="{x0}" y="{y}" width="532" height="29" rx="7" '
                            f'fill="{p["brk"]}" fill-opacity=".16"/><rect x="{x0}" y="{y}" width="4" height="29" rx="2" fill="{p["brk"]}"/></g>')
            else:
                rows.append(f'<rect x="{x0}" y="{y}" width="532" height="29" rx="7" fill="{fill}"/>')
            col = p["brk"] if (after and bad) else (p["rule"] if after else p["fg"])
            rows.append(f'<text x="{x0 + 16}" y="{y + 20}" font-family="{MONO}" font-size="14" fill="{p["muted"]}">Slab {i + 1}</text>')
            mark_ = (" ✓" if not bad else "") if after else ""
            rows.append(f'<text x="{x0 + 200}" y="{y + 20}" font-family="{MONO}" font-size="14" fill="{col}">₹{v:,}{mark_}</text>')
            if after and bad:
                rows.append(f'<text class="hit" style="animation-delay:{0.45 + i * 0.16:.2f}s" x="{x0 + 300}" y="{y + 20}" '
                            f'font-size="13" fill="{p["muted"]}">should be ₹{fees[i]:,}</text>')
        return "".join(rows)
    css = f'''
.scan {{ animation: sc {C}s linear infinite; }}
@keyframes sc {{ 0% {{ transform: translateY(0); opacity: 0; }} 4% {{ opacity: 1; }} 40% {{ transform: translateY(330px); opacity: 1; }} 44%, 100% {{ transform: translateY(330px); opacity: 0; }} }}
.hit {{ opacity: 0; animation: hit {C}s infinite; }}
@keyframes hit {{ 0%, 3% {{ opacity: 0; }} 8%, 92% {{ opacity: 1; }} 100% {{ opacity: 0; }} }}
.rulebox {{ opacity: 0; animation: hit {C}s infinite; animation-delay: 3.2s; }}'''
    body = f'''<rect width="{W}" height="{H}" rx="26" fill="{p["bg"]}" stroke="{p["line"]}"/>
<path d="{t1}" fill="{p["fg"]}"/><path d="{t2}" fill="{p["fg"]}"/>
<text x="1216" y="64" text-anchor="end" font-family="{MONO}" font-size="12" fill="{p["dim"]}">2 issues · 8 rows correct</text>
{table(64, False)}
{table(684, True)}
<rect class="scan" x="684" y="86" width="532" height="40" fill="url(#halo)"/>
<line x1="640" x2="640" y1="40" y2="430" stroke="{p["line"]}" stroke-dasharray="4 6"/>
<g class="rulebox"><rect x="684" y="420" width="532" height="34" rx="10" fill="{p["rule"]}" fill-opacity=".12"/>
<text x="700" y="442" font-family="{MONO}" font-size="13" fill="{p["rule"]}">Rule found: each fee = previous + ₹125</text></g>
<text x="64" y="442" font-size="13" fill="{p["dim"]}">Looks fine at a glance…</text>'''
    return svg(W, H, body, css, p)


def results(theme: str, sora: Outliner) -> str:
    p = PAL[theme]
    W, H = 1280, 250
    cards = [("20,000", "independent test sequences", "all correct (100%)", 1.0, "rule"),
             ("95,000", "real business series", "zero made-up rules", 1.0, "rule"),
             ("96.8%", "precision on 47,585 OEIS", "sequences when it answers", 0.968, "rule"),
             ("0 vs 185", "wrong answers vs a leading", "symbolic-regression tool", 0.08, "brk")]
    out = []
    for k, (big, l1, l2, frac, col) in enumerate(cards):
        x = 32 + k * 312
        b, _ = sora.path(big, 40, x + 26, 92, tracking=-0.03)
        out.append(f'''<g class="rv" style="animation-delay:{k * 0.15:.2f}s">
<rect x="{x}" y="24" width="292" height="202" rx="20" fill="{p["bg2"]}" stroke="{p["line"]}"/>
<path d="{b}" fill="{p[col]}"/>
<text x="{x + 26}" y="128" font-size="15" fill="{p["fg"]}">{l1}</text>
<text x="{x + 26}" y="150" font-size="15" fill="{p["muted"]}">{l2}</text>
<rect x="{x + 26}" y="182" width="240" height="8" rx="4" fill="{p["line"]}"/>
<rect class="bar" style="animation-delay:{0.3 + k * 0.15:.2f}s" x="{x + 26}" y="182" width="{240 * frac:.0f}" height="8" rx="4" fill="{p[col]}"/>
</g>''')
    css = '''
.rv { animation: rv 1s cubic-bezier(.2,.8,.2,1) both; }
@keyframes rv { from { opacity: 0; transform: translateY(14px); } }
.bar { transform-box: fill-box; transform-origin: left; animation: bar 1.6s cubic-bezier(.2,.8,.2,1) both; }
@keyframes bar { from { transform: scaleX(0); } }'''
    return svg(W, H, "".join(out), css, p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", required=True, help="directory containing Syne.ttf and Sora.ttf (variable fonts)")
    a = ap.parse_args()
    fd = Path(a.fonts)
    syne, sora = Outliner(fd / "Syne.ttf", 800), Outliner(fd / "Sora.ttf", 650)
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in ("dark", "light"):
        (OUT / f"banner-{theme}.svg").write_text(banner(theme, syne, sora))
        (OUT / f"how-{theme}.svg").write_text(how(theme, sora))
        (OUT / f"before-after-{theme}.svg").write_text(before_after(theme, sora))
        (OUT / f"results-{theme}.svg").write_text(results(theme, sora))
    for f in sorted(OUT.glob("*.svg")):
        print(f"{f.name:28s} {f.stat().st_size:>7,} bytes")


if __name__ == "__main__":
    main()
