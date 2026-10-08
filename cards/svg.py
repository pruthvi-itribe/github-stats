"""Render static SVG cards. No foreignObject and no animation, so they draw the
same in every browser, the GitHub mobile app, and link previews."""

from typing import Dict, List, Sequence, Tuple
from xml.sax.saxutils import escape

from .data import YearStats

WIDTH = 480
PAD = 24
FONT = "-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif"

THEMES = {
    "light": {"bg": "#ffffff", "border": "#d0d7de", "ink": "#1f2328",
              "muted": "#59636e", "accent": "#0969da", "track": "#eff2f5"},
    "dark": {"bg": "#0d1117", "border": "#30363d", "ink": "#e6edf3",
             "muted": "#9198a1", "accent": "#4493f8", "track": "#161b22"},
}

MIN_VISIBLE_SHARE = 0.005

AREA_PALETTE = ("#0969da", "#bf8700", "#8250df", "#1a7f37", "#cf222e", "#6e7781")


def _frame(height: int, theme: dict, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" font-family="{FONT}">'
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="8" '
        f'fill="{theme["bg"]}" stroke="{theme["border"]}"/>{body}</svg>'
    )


def _heading(title: str, subtitle: str, theme: dict) -> str:
    return (
        f'<text x="{PAD}" y="34" font-size="15" font-weight="600" fill="{theme["ink"]}">'
        f'{escape(title)}</text>'
        f'<text x="{PAD}" y="53" font-size="11.5" fill="{theme["muted"]}">'
        f'{escape(subtitle)}</text>'
    )


def _stat_tiles(stats: YearStats, theme: dict) -> str:
    tiles = (
        (f"{stats.contributions:,}", "contributions"),
        (f"{stats.commits:,}", "commits"),
        (f"{stats.pull_requests:,}", "pull requests"),
        (f"{stats.reviews:,}", "reviews"),
        (f"{stats.active_days}", "active days"),
    )
    step = (WIDTH - 2 * PAD) / len(tiles)
    parts = []
    for i, (value, label) in enumerate(tiles):
        x = PAD + i * step
        parts.append(
            f'<text x="{x:.1f}" y="92" font-size="22" font-weight="600" '
            f'fill="{theme["ink"]}">{escape(value)}</text>'
            f'<text x="{x:.1f}" y="110" font-size="11" fill="{theme["muted"]}">'
            f'{escape(label)}</text>'
        )
    return "".join(parts)


def _sparkline(weekly: Sequence[int], theme: dict, top: int, height: int) -> str:
    if not weekly:
        return ""
    peak = max(max(weekly), 1)
    gap = 2
    bar_w = (WIDTH - 2 * PAD - gap * (len(weekly) - 1)) / len(weekly)
    parts = []
    for i, count in enumerate(weekly):
        h = max(2.0, height * count / peak)
        x = PAD + i * (bar_w + gap)
        fill = theme["accent"] if count else theme["track"]
        parts.append(
            f'<rect x="{x:.1f}" y="{top + height - h:.1f}" width="{bar_w:.1f}" '
            f'height="{h:.1f}" rx="1.5" fill="{fill}"/>'
        )
    label_y = top + height + 16
    parts.append(
        f'<text x="{PAD}" y="{label_y}" font-size="10.5" fill="{theme["muted"]}">'
        f'52 weeks ago</text>'
        f'<text x="{WIDTH - PAD}" y="{label_y}" font-size="10.5" text-anchor="end" '
        f'fill="{theme["muted"]}">this week</text>'
    )
    return "".join(parts)


def activity_card(stats: YearStats, theme_name: str) -> str:
    theme = THEMES[theme_name]
    body = (
        _heading("Last 12 months on GitHub",
                 f"Includes private repositories · {stats.longest_streak}-day best streak", theme)
        + _stat_tiles(stats, theme)
        + _sparkline(stats.weekly, theme, top=132, height=44)
    )
    return _frame(204, theme, body)


def _share_bar(shares: List[Tuple[str, float]], colors: Dict[str, str], top: int) -> str:
    parts = ['<clipPath id="bar"><rect x="%d" y="%d" width="%d" height="10" rx="5"/></clipPath>'
             % (PAD, top, WIDTH - 2 * PAD), '<g clip-path="url(#bar)">']
    x = float(PAD)
    for label, fraction in shares:
        w = (WIDTH - 2 * PAD) * fraction
        parts.append(f'<rect x="{x:.1f}" y="{top}" width="{w + 0.5:.1f}" height="10" '
                     f'fill="{colors[label]}"/>')
        x += w
    parts.append("</g>")
    return "".join(parts)


def _legend(shares: List[Tuple[str, float]], colors: Dict[str, str], theme: dict, top: int) -> str:
    col_w = (WIDTH - 2 * PAD) / 2
    parts = []
    for i, (label, fraction) in enumerate(shares):
        x = PAD + (i % 2) * col_w
        y = top + (i // 2) * 22
        parts.append(
            f'<circle cx="{x + 5:.1f}" cy="{y - 4}" r="5" fill="{colors[label]}"/>'
            f'<text x="{x + 16:.1f}" y="{y}" font-size="12" fill="{theme["ink"]}">'
            f'{escape(label)} <tspan fill="{theme["muted"]}">{fraction * 100:.0f}%</tspan></text>'
        )
    return "".join(parts)


def share_card(title: str, subtitle: str, shares: List[Tuple[str, float]],
               colors: Dict[str, str], theme_name: str) -> str:
    theme = THEMES[theme_name]
    shares = [(label, f) for label, f in shares if f >= MIN_VISIBLE_SHARE]
    rows = (len(shares) + 1) // 2
    height = 112 + rows * 22
    body = (
        _heading(title, subtitle, theme)
        + _share_bar(shares, colors, top=70)
        + _legend(shares, colors, theme, top=106)
    )
    return _frame(height, theme, body)
