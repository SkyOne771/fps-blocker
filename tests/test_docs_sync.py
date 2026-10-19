from pathlib import Path
import tempfile
import unittest

from tools.check_docs_sync import broken_links, documentation_changed, event_base, needs_documentation


class DocumentationTests(unittest.TestCase):
    def test_runtime_and_workflow_changes_require_docs(self):
        for path in ["fps_blocker/controller.py", "tools/amd_freesync.py", "start.bat", ".github/workflows/check.yml"]:
            with self.subTest(path=path):
                self.assertTrue(needs_documentation([path]))
        self.assertFalse(needs_documentation(["assets/icon.svg", "tests/test_controller.py"]))

    def test_contributor_notes_alone_do_not_satisfy_behavior_docs(self):
        self.assertFalse(documentation_changed(["CONTRIBUTING.md", "AGENTS.md"]))
        self.assertTrue(documentation_changed(["README.md"]))
        self.assertTrue(documentation_changed(["docs/architecture.md"]))

    def test_event_base_handles_pr_push_and_first_push(self):
        self.assertEqual(event_base({"pull_request": {"base": {"sha": "abc"}}}), "abc")
        self.assertEqual(event_base({"before": "def"}), "def")
        self.assertIsNone(event_base({"before": "0" * 40}))

    def test_link_checker_reports_missing_local_images_and_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text('[missing](docs/missing.md)\n<img src="assets/missing.png">\n[remote](https://example.com)')
            (root / "CONTRIBUTING.md").write_text("Contributing")
            errors = broken_links(root)
            self.assertEqual(len(errors), 2)
            self.assertTrue(any("assets/missing.png" in error for error in errors))

    def test_link_checker_accepts_relative_paths_and_ignores_anchors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "README.md").write_text('[guide](docs/guide.md#setup)\n[section](#setup)')
            (root / "CONTRIBUTING.md").write_text('[readme](README.md)')
            (root / "docs/guide.md").write_text('[home](../README.md)')
            self.assertEqual(broken_links(root), [])
