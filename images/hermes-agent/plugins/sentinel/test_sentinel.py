import importlib.util
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

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
            self.assertEqual(sentinel.directive(json.dumps({"verdict": verdict, "reason": "bulk"}))["action"], "approve")

    def test_unreadable_reply_asks(self):
        for text in ("", "sure, looks fine", '{"reason": "no verdict"}'):
            self.assertEqual(sentinel.directive(text)["action"], "approve")


class Hook(unittest.TestCase):
    def hook(self, complete):
        ctx = SimpleNamespace(llm=SimpleNamespace(complete=complete), hooks={},
                              register_auxiliary_task=lambda *a, **k: None,
                              register_hook=lambda name, fn: ctx.hooks.__setitem__(name, fn))
        sentinel.register(ctx)
        return ctx.hooks["pre_tool_call"]

    def test_failed_review_asks(self):
        def raises(*a, **k):
            raise TimeoutError
        for complete in (raises, lambda *a, **k: SimpleNamespace(text=None), lambda *a, **k: object()):
            directive = self.hook(complete)(tool_name="mcp__sure__update_transaction", args={})
            self.assertEqual(directive["action"], "approve")

    def test_reads_skip_the_reviewer(self):
        def raises(*a, **k):
            raise AssertionError("reviewer called")
        self.assertIsNone(self.hook(raises)(tool_name="mcp__sure__get_accounts", args={}))


if __name__ == "__main__":
    unittest.main()
