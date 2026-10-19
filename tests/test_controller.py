from types import SimpleNamespace
import unittest

from fps_blocker.controller import Controller
from fps_blocker.windows import DisplayError, Foreground


class FakeWindows:
    def __init__(self):
        self.front = Foreground("chrome.exe", "display1")
        self.rates = {"display1": 144, "display2": 165}
        self.changes = []
        self.fail = False

    def foreground(self):
        return self.front

    def mode(self, display):
        return SimpleNamespace(frequency=self.rates[display])

    def limited_mode(self, display, maximum):
        if maximum < 60:
            raise DisplayError("Unsupported refresh rate")
        return self.mode(display), SimpleNamespace(frequency=60)

    def apply(self, display, mode):
        if self.fail:
            raise DisplayError("Change failed")
        self.rates[display] = mode.frequency
        self.changes.append((display, mode.frequency))


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.windows = FakeWindows()
        self.controller = Controller(self.windows)

    def tick(self, enabled=True, rate=60):
        return self.controller.tick(enabled, {"chrome.exe"}, rate)

    def test_browser_focus_limits_once_and_switching_away_restores(self):
        self.tick()
        self.tick()
        self.windows.front = Foreground("notepad.exe", "display1")
        self.tick()
        self.assertEqual(self.windows.changes, [("display1", 60), ("display1", 144)])

    def test_moving_browser_restores_old_monitor_before_limiting_new(self):
        self.tick()
        self.windows.front = Foreground("chrome.exe", "display2")
        self.tick()
        self.assertEqual(self.windows.changes, [("display1", 60), ("display1", 144), ("display2", 60)])
        self.tick(False)
        self.assertEqual(self.windows.rates, {"display1": 144, "display2": 165})

    def test_unsupported_rate_never_changes_display(self):
        with self.assertRaises(DisplayError):
            self.tick(rate=30)
        self.assertEqual(self.windows.changes, [])
        self.assertIsNone(self.controller.active)

    def test_already_slow_display_is_not_raised(self):
        self.windows.rates["display1"] = 50
        self.tick()
        self.assertEqual(self.windows.changes, [])

    def test_failed_restore_retains_original_for_retry(self):
        self.tick()
        self.windows.fail = True
        with self.assertRaises(DisplayError):
            self.tick(False)
        self.assertIsNotNone(self.controller.active)
        self.windows.fail = False
        self.tick(False)
        self.assertEqual(self.windows.rates["display1"], 144)

    def test_unknown_foreground_restores(self):
        self.tick()
        self.windows.front = None
        self.tick()
        self.assertEqual(self.windows.rates["display1"], 144)

    def test_failed_apply_does_not_mark_limit_active(self):
        self.windows.fail = True
        with self.assertRaises(DisplayError):
            self.tick()
        self.assertIsNone(self.controller.active)


if __name__ == "__main__":
    unittest.main()
