"""Focus policy separated from Win32 for testing."""
from .windows import DisplayError


class Controller:
    def __init__(self, windows):
        self.windows = windows
        self.active = None

    def restore(self):
        if self.active:
            display, original, _ = self.active
            self.windows.apply(display, original)
            self.active = None

    def tick(self, enabled, browsers, maximum):
        foreground = self.windows.foreground() if enabled else None
        display = foreground.display if foreground and foreground.executable in browsers else None
        if self.active and (display != self.active[0] or maximum != self.active[2]):
            self.restore()
        if not enabled:
            return "Paused — original refresh rate restored."
        if not display:
            return "Watching — switch to a selected browser to limit its display."
        if not self.active:
            original, target = self.windows.limited_mode(display, maximum)
            if original.frequency > target.frequency:
                self.windows.apply(display, target)
                self.active = (display, original, maximum)
            else:
                return f"Already at {original.frequency} Hz — no change needed."
        current = self.windows.mode(display)
        if current is None:
            raise DisplayError("The active display is unavailable. Pause and reconnect it.")
        return f"Browsing limit active · {current.frequency} Hz · {foreground.executable}"
