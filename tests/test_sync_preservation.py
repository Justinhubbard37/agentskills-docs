"""Offline regression tests for the preservation gate (stdlib only)."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import sync_agentskills as sync


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.name = "specification.md"
        self.url = "https://agentskills.io/specification"
        self.old = sync.normalize_markdown("# Specification\n\n## Rules\n\n" + "Existing rule. " * 40 + "\n", self.url)
        (self.root / self.name).write_text(self.old, encoding="utf-8")
        self.previous = {"documents": [{"file_name": self.name, "canonical_md_url": self.url + ".md"}]}
        self.before = {"docs/specification.mdx": "a" * 40}
        self.after = dict(self.before)

    def document(self, content):
        return sync.RemoteDocument("Specification", "", self.url + ".md", self.url, self.name, content)

    def gate(self, content=None, changed_source=False, metadata=None, before=None, after=None):
        content = self.old if content is None else content
        doc = self.document(content)
        diff = sync.compute_diff(self.root, {self.name: content}, [self.name])
        current = {"docs/specification.mdx": "b" * 40} if changed_source else self.after
        return sync.preservation_gate(self.root, self.previous, [doc], diff, metadata or [],
                                      self.before if before is None else before,
                                      current if after is None else after)

    def test_no_change(self):
        result = self.gate()
        self.assertFalse(result["proposal_allowed"])
        self.assertEqual(result["preservation_blockers"], [])
        self.assertEqual(result["preservation_classifications"][self.name], "unchanged")

    def test_export_drift_with_unchanged_source(self):
        result = self.gate(self.old.replace("Existing rule.", "Existing rule. "))
        self.assertFalse(result["proposal_allowed"])
        self.assertEqual(result["preservation_classifications"][self.name], "uncorroborated_export_drift")

    def test_source_backed_addition_eligible(self):
        result = self.gate(self.old + "\nNew rule.\n", changed_source=True)
        self.assertTrue(result["proposal_allowed"])
        self.assertEqual(result["preservation_classifications"][self.name], "source_backed_candidate")

    def test_source_change_without_export_change(self):
        result = self.gate(changed_source=True)
        self.assertFalse(result["proposal_allowed"])
        self.assertTrue(result["preservation_blockers"])

    def test_truncation_even_with_source_change(self):
        result = self.gate(sync.normalize_markdown("# Specification\n\n## Rules\n", self.url), changed_source=True)
        self.assertFalse(result["proposal_allowed"])
        self.assertEqual(result["preservation_classifications"][self.name], "possible_content_loss")

    def test_missing_heading_even_if_size_increases(self):
        result = self.gate(self.old.replace("## Rules", "## Different") + "Extra text " * 100, changed_source=True)
        self.assertFalse(result["proposal_allowed"])

    def test_missing_source_evidence(self):
        result = self.gate(self.old + "Extra.\n", after={})
        self.assertFalse(result["proposal_allowed"])
        self.assertEqual(result["preservation_classifications"][self.name], "source_evidence_missing")

    def test_local_integrity_mismatch(self):
        result = self.gate(self.old + "New.\n", changed_source=True, metadata=["specification.md:local_sha256"])
        self.assertFalse(result["proposal_allowed"])

    def test_removed_page(self):
        diff = {"changed": [], "added": [], "removed": [self.name]}
        result = sync.preservation_gate(self.root, self.previous, [], diff, [], self.before, self.after)
        self.assertFalse(result["proposal_allowed"])
        self.assertEqual(result["preservation_classifications"][self.name], "scope_removed")

    def test_added_page(self):
        diff = {"changed": [], "added": ["new.md"], "removed": []}
        result = sync.preservation_gate(self.root, self.previous, [self.document(self.old)], diff, [], self.before, self.after)
        self.assertFalse(result["proposal_allowed"])
        self.assertEqual(result["preservation_classifications"]["new.md"], "scope_added")

    def test_mixed_batch_blocks_entire_update(self):
        doc = self.document(self.old + "New.\n")
        diff = {"changed": [self.name], "added": [], "removed": ["clients.md"]}
        result = sync.preservation_gate(self.root, self.previous, [doc], diff, [], self.before,
                                       {"docs/specification.mdx": "b" * 40})
        self.assertEqual(result["preservation_classifications"][self.name], "source_backed_candidate")
        self.assertFalse(result["proposal_allowed"])

    def test_dynamic_pages_require_review(self):
        for name in ("home.md", "clients.md"):
            with self.subTest(name=name):
                url = "https://agentskills.io/" + name[:-3]
                old = sync.normalize_markdown("# Clients\n\n## Directory\n\n" + "Client data. " * 40, url)
                (self.root / name).write_text(old, encoding="utf-8")
                previous = {"documents": [{"file_name": name, "canonical_md_url": url + ".md"}]}
                doc = sync.RemoteDocument("Clients", "", url + ".md", url, name, old + "New client.\n")
                before = {"docs/" + name[:-3] + ".mdx": "a" * 40, "docs/snippets/clients.jsx": "b" * 40}
                after = {**before, "docs/snippets/clients.jsx": "c" * 40}
                result = sync.preservation_gate(self.root, previous, [doc],
                    {"changed": [name], "added": [], "removed": []}, [], before, after)
                self.assertFalse(result["proposal_allowed"])
                self.assertEqual(result["preservation_classifications"][name], "dynamic_export_review")

    def test_blocked_write_preserves_snapshot(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "AGENTSKILLS_SYNC_WRITE": "1"}):
            with self.assertRaisesRegex(RuntimeError, "Preservation gate"):
                sync.apply_update(self.root, self.previous, [self.document(self.old + "New.\n")],
                                  "", "b" * 40, {"proposal_allowed": False})
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_colliding_local_filenames_fail(self):
        with self.assertRaisesRegex(RuntimeError, "collide"):
            sync.parse_llms("- [One](https://agentskills.io/foo-bar.md): x\n"
                            "- [Two](https://agentskills.io/foo/bar.md): y")


if __name__ == "__main__":
    unittest.main()
