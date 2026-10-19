from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import amd_freesync


class FakeADL:
    def __init__(self):
        self.entry = {"name": "AORUS FO32U2P", "windows_display": "display1", "current": 7}
        self.changes = []
        self.closed = False
        self.fail = False

    def displays(self):
        return [self.entry.copy()]

    def set(self, entry, value):
        self.changes.append(value)
        if self.fail and value == 0:
            raise RuntimeError("Driver rejected setting")
        self.entry["current"] = value
        return {"current": value}

    def close(self):
        self.closed = True


class FreeSyncTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.backup = Path(self.directory.name) / "backup.json"
        self.adl = FakeADL()

    def run_command(self, action):
        with patch.object(amd_freesync, "ADL", return_value=self.adl), patch(
                "sys.argv", ["amd_freesync", action, "--backup", str(self.backup)]), redirect_stdout(io.StringIO()):
            amd_freesync.main()

    def test_disable_backs_up_original_and_restore_recovers_it(self):
        self.run_command("--disable")
        self.assertEqual(json.loads(self.backup.read_text())["current"], 7)
        self.assertEqual(self.adl.entry["current"], 0)
        self.run_command("--restore")
        self.assertEqual(self.adl.entry["current"], 7)
        self.assertTrue(self.adl.closed)

    def test_existing_backup_is_not_overwritten(self):
        self.backup.write_text("original backup")
        with self.assertRaises(FileExistsError):
            self.run_command("--disable")
        self.assertEqual(self.backup.read_text(), "original backup")
        self.assertEqual(self.adl.changes, [])
        self.assertTrue(self.adl.closed)

    def test_failed_change_rolls_back(self):
        self.adl.fail = True
        with self.assertRaises(RuntimeError):
            self.run_command("--disable")
        self.assertEqual(self.adl.changes, [0, 7])
        self.assertEqual(self.adl.entry["current"], 7)

    def test_wrong_monitor_backup_is_refused(self):
        self.backup.write_text(json.dumps({"name": "other", "windows_display": "display1", "current": 7}))
        with self.assertRaises(RuntimeError):
            self.run_command("--restore")
        self.assertEqual(self.adl.changes, [])

    def test_already_disabled_keeps_original_backup(self):
        self.adl.entry["current"] = 0
        self.backup.write_text("original backup")
        self.run_command("--disable")
        self.assertEqual(self.backup.read_text(), "original backup")
        self.assertEqual(self.adl.changes, [])


if __name__ == "__main__":
    unittest.main()
