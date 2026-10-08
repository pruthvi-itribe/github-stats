import unittest

from cards.data import RepoCommits, longest_streak, parse, share_by
from cards.svg import activity_card, share_card


def repo(name, commits, language="TypeScript"):
    return RepoCommits(name=name, commits=commits, language=language, color="#3178c6")


def viewer(days, repos):
    return {
        "name": "Test User", "login": "test",
        "contributionsCollection": {
            "totalCommitContributions": 10, "totalPullRequestContributions": 2,
            "totalPullRequestReviewContributions": 1,
            "totalRepositoriesWithContributedCommits": len(repos),
            "contributionCalendar": {"totalContributions": 99, "weeks": [
                {"contributionDays": [{"contributionCount": c} for c in days[i:i + 7]]}
                for i in range(0, len(days), 7)]},
            "commitContributionsByRepository": repos,
        },
    }


class LongestStreakTest(unittest.TestCase):
    def test_counts_longest_run_of_active_days(self):
        self.assertEqual(longest_streak([1, 1, 0, 3, 2, 5, 0]), 3)

    def test_empty_and_idle(self):
        self.assertEqual(longest_streak([]), 0)
        self.assertEqual(longest_streak([0, 0]), 0)


class ShareByTest(unittest.TestCase):
    def test_folds_tail_into_other_and_sums_to_one(self):
        repos = (repo("a", 60), repo("b", 30, "Python"), repo("c", 10, "Dart"))
        shares = share_by(repos, key=lambda r: r.language, top=2)
        self.assertEqual([label for label, _ in shares], ["TypeScript", "Python", "Other"])
        self.assertAlmostEqual(sum(f for _, f in shares), 1.0)

    def test_blank_key_is_excluded(self):
        repos = (repo("a", 50), repo("skip", 50))
        shares = share_by(repos, key=lambda r: "" if r.name == "skip" else "A", top=3)
        self.assertEqual(shares, [("A", 1.0)])

    def test_no_commits_gives_no_shares(self):
        self.assertEqual(share_by((), key=lambda r: r.language, top=3), [])


class ParseTest(unittest.TestCase):
    def test_drops_forks_and_defaults_missing_language(self):
        repos = [
            {"repository": {"nameWithOwner": "me/own", "isFork": False, "primaryLanguage": None},
             "contributions": {"totalCount": 5}},
            {"repository": {"nameWithOwner": "me/fork", "isFork": True,
                            "primaryLanguage": {"name": "Go", "color": "#00ADD8"}},
             "contributions": {"totalCount": 9}},
        ]
        stats = parse(viewer([1, 0, 2, 2, 0, 0, 1], repos))
        self.assertEqual([r.name for r in stats.repo_commits], ["me/own"])
        self.assertEqual(stats.repo_commits[0].language, "Other")
        self.assertEqual((stats.active_days, stats.total_days, stats.longest_streak), (4, 7, 2))
        self.assertEqual(stats.contributions, 99)


class RenderTest(unittest.TestCase):
    def test_cards_are_static_and_escape_text(self):
        stats = parse(viewer([1] * 14, []))
        svg = activity_card(stats, "dark")
        card = share_card("A & B", "sub", [("C<D", 1.0)], {"C<D": "#000"}, "light")
        for out in (svg, card):
            self.assertNotIn("foreignObject", out)
            self.assertNotIn("animation", out)
        self.assertIn("A &amp; B", card)
        self.assertIn("C&lt;D", card)


if __name__ == "__main__":
    unittest.main()
