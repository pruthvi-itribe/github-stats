"""Maps each repository to the area of work it belongs to, so the profile can show
where the year's commits went without naming any private repository.

Repos seen in the last 12 months (commits), for reference:
  1065 cat-trader            533 disclosed (public)     254 investorstribe/charts
   172 iron-condors-backend  158 iron-condors-ui        135 best-calculators
   135 swiggy-options         92 buildnovate-buildshot    80 mindful-backtest
    42 dd-orders-nestjs       42 jsontoon                 35 home-monitor
    26 spy-strangle-lab       23 robinhood-investments    17 dallaspuram-ui
    16 investorstribe/tralk-infra   15 claude-config      15 investorstribe/kline-charts
    10 Swathaha/swaartha-ui    8 investorstribe/binance-mcp-server
     6 decoded.paisa            6 tradingagents-india     5 dallaspuram-menu
  (plus a long tail of 1-5 commit repos)
"""

# Labels shown on the card, in display order. Keep them short (they sit in a legend).
AREAS = (
    "Trading platforms",
    "Quant & options research",
    "LLM & agent tooling",
    "Products & client builds",
    "Infra & DevOps",
)

# Repos that should not count toward any area (profile plumbing, personal finance notes).
IGNORED = {"github-stats", "pruthvi-itribe"}


def area_for(repo_name: str) -> str:
    """Return one of AREAS for a repo ('owner/name'), or '' to leave it out.

    TODO(Pruthvi): decide which bucket each repo belongs in. This is the part that
    shapes what a visitor reads into the card, e.g. whether cat-trader's 1,065
    commits show as "Quant & options research" (true, but it will dominate the
    bar) or whether some of it is platform work.
    """
    name = repo_name.split("/")[-1]
    if name in IGNORED:
        return ""
    return ""
