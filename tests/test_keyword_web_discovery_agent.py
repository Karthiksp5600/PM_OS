import tempfile
import unittest
from pathlib import Path

from productpilot.agents.web_problem_discovery_agent import KeywordWebDiscoveryAgent


class KeywordWebDiscoveryAgentTests(unittest.TestCase):
    def test_agent_discovers_problems_from_keyword(self) -> None:
        agent = KeywordWebDiscoveryAgent()
        result = agent.run("project management")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["keyword"], "project management")
        self.assertIsInstance(result["problem_statements"], list)
        self.assertGreaterEqual(len(result["problem_statements"]), 10)
        self.assertTrue(all(isinstance(item, str) and item.strip() for item in result["problem_statements"]))

    def test_agent_reads_context_from_file(self) -> None:
        agent = KeywordWebDiscoveryAgent()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "input.txt"
            path.write_text("project management collaboration planning workload visibility", encoding="utf-8")
            result = agent.run(file_path=path)

            self.assertEqual(result["status"], "success")
            self.assertIsInstance(result["problem_statements"], list)
            self.assertGreaterEqual(len(result["problem_statements"]), 10)

    def test_agent_aggregates_play_store_and_web_sources(self) -> None:
        agent = KeywordWebDiscoveryAgent()
        agent._fetch_search_results = lambda keyword: [
            "Confusing onboarding and poor value discovery",
            "Slow setup and difficult workflow adoption",
        ]
        agent._fetch_app_store_reviews = lambda keyword: [
            "App is frustrating because onboarding takes too long",
            "Reviews mention poor task visibility and confusing navigation",
        ]
        agent._fetch_reddit_x_forums = lambda keyword: [
            "Community posts complain about unclear workflows and too many notifications",
        ]
        agent._fetch_support_ticket_themes = lambda keyword: [
            "Support tickets show repeated issues with missing status visibility",
        ]
        agent._fetch_other_public_sources = lambda keyword: [
            "Users complain about unclear priorities and missing notifications",
        ]

        result = agent.run("project management")

        self.assertIn("web_search", result["sources"])
        self.assertIn("app_store_reviews", result["sources"])
        self.assertIn("reddit_x_forums", result["sources"])
        self.assertIn("support_ticket_themes", result["sources"])
        self.assertIn("other_public_sources", result["sources"])
        self.assertGreaterEqual(len(result["problem_statements"]), 5)
        self.assertIn("onboarding", " ".join(result["problem_statements"]).lower())


if __name__ == "__main__":
    unittest.main()
