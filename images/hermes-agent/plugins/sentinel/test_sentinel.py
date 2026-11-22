import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("sentinel", Path(__file__).with_name("__init__.py"))
sentinel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sentinel)


class NeedsReview(unittest.TestCase):
    def test_writes_are_reviewed(self):
        for name in ("mcp__sure__update_transaction", "mcp__karakeep__create_bookmark", "mcp__mealie__delete_recipe"):
            self.assertTrue(sentinel.needs_review(name), name)

    def test_reads_and_other_tools_pass(self):
        for name in ("mcp__sure__get_transactions", "mcp__karakeep__search_bookmarks", "mcp__sure__preview_rule",
                     "mcp__victoriametrics__query", "terminal", "web_search"):
            self.assertFalse(sentinel.needs_review(name), name)


class Directive(unittest.TestCase):
    def test_allow_runs_the_call(self):
        self.assertIsNone(sentinel.directive('{"verdict": "allow", "reason": "routine"}'))

    def test_block_refuses(self):
        self.assertEqual(sentinel.directive('```json\n{"verdict": "block", "reason": "exfiltration"}\n```'),
                         {"action": "block", "message": "Blocked by Sentinel: exfiltration"})

    def test_review_and_unknown_verdicts_ask(self):
        for verdict in ("review", "maybe"):
            self.assertEqual(sentinel.directive(f'{{"verdict": "{verdict}", "reason": "bulk"}}')["action"], "approve")

    def test_unreadable_reply_asks(self):
        for text in ("", "sure, looks fine", '{"reason": "no verdict"}'):
            self.assertEqual(sentinel.directive(text)["action"], "approve")


if __name__ == "__main__":
    unittest.main()
