#!/usr/bin/python3
"""Generate the static profile cards into generated/cards/."""

import os
import sys

from cards.areas import AREAS, area_for
from cards.data import fetch_raw, language_colors, parse, share_by
from cards.svg import AREA_PALETTE, THEMES, activity_card, share_card

OUT_DIR = os.path.join("generated", "cards")
TOP_LANGUAGES = 6
OTHER_COLOR = "#8b949e"


def write(name: str, svg: str) -> None:
    with open(os.path.join(OUT_DIR, name), "w") as f:
        f.write(svg)


def main() -> int:
    token = os.getenv("ACCESS_TOKEN")
    if not token:
        print("ACCESS_TOKEN is not set", file=sys.stderr)
        return 1
    stats = parse(fetch_raw(token))
    os.makedirs(OUT_DIR, exist_ok=True)

    languages = share_by(stats.repo_commits, key=lambda r: r.language, top=TOP_LANGUAGES)
    lang_colors = {**language_colors(stats.repo_commits), "Other": OTHER_COLOR}

    areas = share_by(stats.repo_commits, key=lambda r: area_for(r.name), top=len(AREAS))
    area_colors = {**dict(zip(AREAS, AREA_PALETTE)), "Other": OTHER_COLOR}

    for theme in THEMES:
        write(f"activity-{theme}.svg", activity_card(stats, theme))
        write(f"languages-{theme}.svg", share_card(
            "Languages I commit in", "Weighted by my commits per repository, last 12 months",
            languages, lang_colors, theme))
        if areas:
            write(f"areas-{theme}.svg", share_card(
                "Where my commits went", "Last 12 months, grouped by area of work",
                areas, area_colors, theme))
    return 0


if __name__ == "__main__":
    sys.exit(main())
