"""Zero-dependency chart rendering (SVG).

Matplotlib is a 40 MB dependency for what is, in the end, a handful of
polylines. Everything here is generated as plain SVG text with the
standard library, which keeps the whole toolkit installable with
``git clone`` and nothing else -- and makes the output diffable, since SVG
is just text.

Two chart types cover every figure this project needs: a line chart for
curves and a bar chart for distributions.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

PALETTE = ["#1f4e79", "#c05000", "#2e7d32", "#8e24aa",
           "#00838f", "#6d4c41", "#ad1457", "#455a64"]

W, H = 760, 460
ML, MR, MT, MB = 74, 24, 56, 74


def _scale(v: float, d0: float, d1: float, p0: float, p1: float) -> float:
    if d1 == d0:
        return (p0 + p1) / 2
    return p0 + (v - d0) / (d1 - d0) * (p1 - p0)


def _ticks(lo: float, hi: float, n: int = 5) -> list[float]:
    if hi == lo:
        return [lo]
    return [lo + (hi - lo) * i / (n - 1) for i in range(n)]


def _fmt(v: float) -> str:
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    if abs(v) >= 10:
        return f"{v:.0f}"
    if abs(v) >= 1:
        return f"{v:.1f}"
    return f"{v:.2f}"


def _escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;"))


def _frame(title: str, xlabel: str, ylabel: str,
           x_domain: tuple[float, float], y_domain: tuple[float, float]) -> list[str]:
    """Axes, gridlines, ticks and labels -- identical for both chart types."""
    out: list[str] = []
    out.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#ffffff"/>')
    out.append(f'<text x="{ML}" y="26" font-family="sans-serif" font-size="15" '
               f'font-weight="bold" fill="#1f4e79">{_escape(title)}</text>')

    x0, x1 = x_domain
    y0, y1 = y_domain
    # horizontal gridlines + y ticks
    for t in _ticks(y0, y1):
        py = _scale(t, y0, y1, H - MB, MT)
        out.append(f'<line x1="{ML}" y1="{py:.1f}" x2="{W - MR}" y2="{py:.1f}" '
                   f'stroke="#e3e8ef" stroke-width="1"/>')
        out.append(f'<text x="{ML - 8}" y="{py + 4:.1f}" text-anchor="end" '
                   f'font-family="sans-serif" font-size="11" fill="#666">{_fmt(t)}</text>')
    # x ticks
    for t in _ticks(x0, x1):
        px = _scale(t, x0, x1, ML, W - MR)
        out.append(f'<text x="{px:.1f}" y="{H - MB + 18}" text-anchor="middle" '
                   f'font-family="sans-serif" font-size="11" fill="#666">{_fmt(t)}</text>')

    out.append(f'<line x1="{ML}" y1="{H - MB}" x2="{W - MR}" y2="{H - MB}" '
               f'stroke="#8a94a6" stroke-width="1.2"/>')
    out.append(f'<line x1="{ML}" y1="{MT}" x2="{ML}" y2="{H - MB}" '
               f'stroke="#8a94a6" stroke-width="1.2"/>')
    out.append(f'<text x="{(ML + W - MR) / 2:.0f}" y="{H - 22}" text-anchor="middle" '
               f'font-family="sans-serif" font-size="12" fill="#333">{_escape(xlabel)}</text>')
    out.append(f'<text x="16" y="{(MT + H - MB) / 2:.0f}" text-anchor="middle" '
               f'font-family="sans-serif" font-size="12" fill="#333" '
               f'transform="rotate(-90 16 {(MT + H - MB) / 2:.0f})">{_escape(ylabel)}</text>')
    return out


def _legend(names: Sequence[str], x: float, y: float) -> list[str]:
    out: list[str] = []
    for i, name in enumerate(names):
        yy = y + i * 18
        color = PALETTE[i % len(PALETTE)]
        out.append(f'<line x1="{x}" y1="{yy}" x2="{x + 22}" y2="{yy}" '
                   f'stroke="{color}" stroke-width="2.4"/>')
        out.append(f'<text x="{x + 28}" y="{yy + 4}" font-family="sans-serif" '
                   f'font-size="11" fill="#333">{_escape(name)}</text>')
    return out


def line_chart(series: Mapping[str, tuple[Sequence[float], Sequence[float]]],
               out: str | Path, title: str = "", xlabel: str = "",
               ylabel: str = "", legend_at: str = "right") -> Path:
    """Draw one or more ``(xs, ys)`` series as an SVG line chart."""
    if not series:
        raise ValueError("series must not be empty")
    xs_all = [x for xs, _ in series.values() for x in xs]
    ys_all = [y for _, ys in series.values() for y in ys]
    x0, x1 = min(xs_all), max(xs_all)
    y0, y1 = min(ys_all), max(ys_all)
    if y1 == y0:
        y1 = y0 + 1
    pad = (y1 - y0) * 0.08
    y0 -= pad
    y1 += pad

    body = _frame(title, xlabel, ylabel, (x0, x1), (y0, y1))
    for i, (name, (xs, ys)) in enumerate(series.items()):
        color = PALETTE[i % len(PALETTE)]
        pts = " ".join(
            f"{_scale(x, x0, x1, ML, W - MR):.1f},{_scale(y, y0, y1, H - MB, MT):.1f}"
            for x, y in zip(xs, ys)
        )
        body.append(f'<polyline points="{pts}" fill="none" stroke="{color}" '
                    f'stroke-width="2.2" stroke-linejoin="round"/>')

    lx = W - MR - 150 if legend_at == "right" else ML + 12
    ly = MT + 14 if legend_at == "right" else H - MB - 18 * len(series) - 6
    body.extend(_legend(list(series), lx, ly))

    body.append("</svg>")
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">')
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([head] + body), encoding="utf-8")
    return path


def bar_chart(xs: Sequence[float], ys: Sequence[float], out: str | Path,
              title: str = "", xlabel: str = "", ylabel: str = "",
              marker: tuple[float, str] | None = None) -> Path:
    """Vertical bars, optionally with a dashed vertical marker line."""
    if len(xs) != len(ys) or not xs:
        raise ValueError("xs and ys must be non-empty and the same length")
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(0.0, min(ys)), max(ys) * 1.08 or 1.0

    body = _frame(title, xlabel, ylabel, (x0, x1), (y0, y1))
    span = (x1 - x0) or 1.0
    bar_w = max(1.0, (W - ML - MR) / span * 0.82)
    for x, y in zip(xs, ys):
        px = _scale(x, x0, x1, ML, W - MR)
        py = _scale(y, y0, y1, H - MB, MT)
        body.append(f'<rect x="{px - bar_w / 2:.1f}" y="{py:.1f}" '
                    f'width="{bar_w:.1f}" height="{H - MB - py:.1f}" '
                    f'fill="#1f4e79" opacity="0.82"/>')
    if marker:
        mx, label = marker
        px = _scale(mx, x0, x1, ML, W - MR)
        body.append(f'<line x1="{px:.1f}" y1="{MT}" x2="{px:.1f}" y2="{H - MB}" '
                    f'stroke="#c00000" stroke-width="1.6" stroke-dasharray="6 4"/>')
        body.append(f'<text x="{px + 6:.1f}" y="{MT + 14}" font-family="sans-serif" '
                    f'font-size="11" fill="#c00000">{_escape(label)}</text>')

    body.append("</svg>")
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}">')
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([head] + body), encoding="utf-8")
    return path
