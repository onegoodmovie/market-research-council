import copy
import json
import unittest
from pathlib import Path

from market_research_council import ResearchCouncil


ROOT = Path(__file__).resolve().parents[1]


def sample_snapshot():
    return json.loads((ROOT / "data" / "synthetic_snapshot.json").read_text(encoding="utf-8"))


class ResearchCouncilTests(unittest.TestCase):
    def test_all_agents_contribute(self):
        report = ResearchCouncil().run(sample_snapshot())
        self.assertEqual(len(report.evidence), 4)
        self.assertEqual(
            {item.agent for item in report.evidence},
            {"price_structure", "volatility_surface", "positioning", "macro_regime"},
        )

    def test_auditor_flags_strike_migration(self):
        report = ResearchCouncil().run(sample_snapshot())
        self.assertTrue(any("strike migration" in item.message for item in report.audit))

    def test_unverified_oi_is_not_used_in_synthesis(self):
        snapshot = copy.deepcopy(sample_snapshot())
        snapshot["positioning"]["oi_is_lagged"] = False
        report = ResearchCouncil().run(snapshot)
        self.assertTrue(any(item.severity == "critical" for item in report.audit))

    def test_probabilities_sum_to_one_hundred(self):
        report = ResearchCouncil().run(sample_snapshot())
        self.assertEqual(sum(item.probability for item in report.scenarios), 100)

    def test_missing_sections_fail_closed(self):
        snapshot = sample_snapshot()
        del snapshot["macro"]
        with self.assertRaisesRegex(ValueError, "macro"):
            ResearchCouncil().run(snapshot)


if __name__ == "__main__":
    unittest.main()
