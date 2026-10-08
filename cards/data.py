"""Fetch last-12-month contribution data from the GitHub GraphQL API and reduce
it to the plain numbers the profile cards show."""

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Tuple

import requests

GRAPHQL_URL = "https://api.github.com/graphql"
REQUEST_TIMEOUT_S = 30
MAX_REPOS = 100

QUERY = """
query {
  viewer {
    name
    login
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalRepositoriesWithContributedCommits
      contributionCalendar { totalContributions weeks { contributionDays { contributionCount } } }
      commitContributionsByRepository(maxRepositories: %d) {
        repository { nameWithOwner isFork primaryLanguage { name color } }
        contributions { totalCount }
      }
    }
  }
}
""" % MAX_REPOS


@dataclass(frozen=True)
class RepoCommits:
    name: str
    commits: int
    language: str
    color: str


@dataclass(frozen=True)
class YearStats:
    name: str
    contributions: int
    commits: int
    pull_requests: int
    reviews: int
    repos: int
    active_days: int
    total_days: int
    longest_streak: int
    weekly: Tuple[int, ...]
    repo_commits: Tuple[RepoCommits, ...]


def fetch_raw(token: str) -> dict:
    response = requests.post(
        GRAPHQL_URL,
        json={"query": QUERY},
        headers={"Authorization": f"bearer {token}"},
        timeout=REQUEST_TIMEOUT_S,
    )
    response.raise_for_status()
    body = response.json()
    if body.get("errors"):
        raise RuntimeError(f"GitHub GraphQL error: {body['errors'][0].get('message')}")
    return body["data"]["viewer"]


def longest_streak(daily: List[int]) -> int:
    best = run = 0
    for count in daily:
        run = run + 1 if count > 0 else 0
        best = max(best, run)
    return best


def parse(viewer: dict) -> YearStats:
    coll = viewer["contributionsCollection"]
    weeks = coll["contributionCalendar"]["weeks"]
    daily = [d["contributionCount"] for w in weeks for d in w["contributionDays"]]
    weekly = tuple(sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks)
    repos = tuple(
        RepoCommits(
            name=item["repository"]["nameWithOwner"],
            commits=item["contributions"]["totalCount"],
            language=(item["repository"]["primaryLanguage"] or {}).get("name") or "Other",
            color=(item["repository"]["primaryLanguage"] or {}).get("color") or "#8b949e",
        )
        for item in coll["commitContributionsByRepository"]
        if not item["repository"]["isFork"]
    )
    return YearStats(
        name=viewer["name"] or viewer["login"],
        contributions=coll["contributionCalendar"]["totalContributions"],
        commits=coll["totalCommitContributions"],
        pull_requests=coll["totalPullRequestContributions"],
        reviews=coll["totalPullRequestReviewContributions"],
        repos=coll["totalRepositoriesWithContributedCommits"],
        active_days=sum(1 for c in daily if c > 0),
        total_days=len(daily),
        longest_streak=longest_streak(daily),
        weekly=weekly,
        repo_commits=repos,
    )


def share_by(repos: Tuple[RepoCommits, ...], key, top: int) -> List[Tuple[str, float]]:
    """Group commits by key(repo), return the top groups as (label, fraction),
    folding the rest into 'Other'. Fractions sum to 1."""
    totals: Counter = Counter()
    for repo in repos:
        label = key(repo)
        if label:
            totals[label] += repo.commits
    grand = sum(totals.values())
    if grand == 0:
        return []
    ranked = totals.most_common()
    head = ranked[:top]
    rest = sum(count for _, count in ranked[top:])
    if rest:
        head = [*head, ("Other", rest)]
    return [(label, count / grand) for label, count in head]


def language_colors(repos: Tuple[RepoCommits, ...]) -> Dict[str, str]:
    return {repo.language: repo.color for repo in repos}
