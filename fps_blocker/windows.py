"""Small Win32 adapter. No administrator rights or GPU-specific SDK needed."""
import ctypes as c
import os
from ctypes import wintypes as w
from dataclasses import dataclass


class DisplayError(RuntimeError):
    pass


class DEVMODE(c.Structure):
    _fields_ = [
        ("device", c.c_uint16 * 32), ("spec", w.WORD), ("driver", w.WORD),
        ("size", w.WORD), ("extra", w.WORD), ("fields", w.DWORD),
        ("positionX", w.LONG), ("positionY", w.LONG),
        ("orientation", w.DWORD), ("fixedOutput", w.DWORD),
        ("color", w.SHORT), ("duplex", w.SHORT), ("yResolution", w.SHORT),
        ("ttOption", w.SHORT), ("collate", w.SHORT),
        ("form", c.c_uint16 * 32), ("logPixels", w.WORD),
        ("bits", w.DWORD), ("width", w.DWORD), ("height", w.DWORD),
        ("flags", w.DWORD), ("frequency", w.DWORD), ("icmMethod", w.DWORD),
        ("icmIntent", w.DWORD), ("media", w.DWORD), ("dither", w.DWORD),
        ("reserved1", w.DWORD), ("reserved2", w.DWORD),
        ("panningWidth", w.DWORD), ("panningHeight", w.DWORD),
    ]


class MONITORINFO(c.Structure):
    _fields_ = [("size", w.DWORD), ("monitor", w.RECT), ("work", w.RECT),
                ("flags", w.DWORD), ("device", w.WCHAR * 32)]


@dataclass
class Foreground:
    executable: str
    display: str


class Windows:
    def __init__(self):
        if os.name != "nt":
            raise DisplayError("FPS Blocker requires Windows 10 or 11.")
        self.user = c.WinDLL("user32", use_last_error=True)
        self.kernel = c.WinDLL("kernel32", use_last_error=True)
        self.user.GetForegroundWindow.restype = w.HWND
        self.user.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
        self.user.MonitorFromWindow.argtypes = [w.HWND, w.DWORD]
        self.user.MonitorFromWindow.restype = w.HMONITOR
        self.user.GetMonitorInfoW.argtypes = [w.HMONITOR, c.POINTER(MONITORINFO)]
        self.user.EnumDisplaySettingsW.argtypes = [w.LPCWSTR, w.DWORD, c.POINTER(DEVMODE)]
        self.user.ChangeDisplaySettingsExW.argtypes = [w.LPCWSTR, c.POINTER(DEVMODE), w.HWND, w.DWORD, c.c_void_p]
        self.user.ChangeDisplaySettingsExW.restype = w.LONG
        self.kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        self.kernel.OpenProcess.restype = w.HANDLE
        self.kernel.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
        self.kernel.CloseHandle.argtypes = [w.HANDLE]

    def foreground(self):
        hwnd = self.user.GetForegroundWindow()
        if not hwnd:
            return None
        pid = w.DWORD()
        self.user.GetWindowThreadProcessId(hwnd, c.byref(pid))
        handle = self.kernel.OpenProcess(0x1000, False, pid.value)
        if not handle:
            return None
        try:
            path, size = c.create_unicode_buffer(32768), w.DWORD(32768)
            if not self.kernel.QueryFullProcessImageNameW(handle, 0, path, c.byref(size)):
                return None
        finally:
            self.kernel.CloseHandle(handle)
        info = MONITORINFO()
        info.size = c.sizeof(info)
        monitor = self.user.MonitorFromWindow(hwnd, 2)
        if not self.user.GetMonitorInfoW(monitor, c.byref(info)):
            return None
        return Foreground(os.path.basename(path.value).lower(), info.device)

    def mode(self, display, index=0xFFFFFFFF):
        mode = DEVMODE()
        mode.size = c.sizeof(mode)
        if not self.user.EnumDisplaySettingsW(display, index, c.byref(mode)):
            return None
        return mode

    def limited_mode(self, display, maximum):
        current = self.mode(display)
        if current is None:
            raise DisplayError("Cannot read the display mode. Reconnect the display and try again.")
        candidates = []
        index = 0
        while (mode := self.mode(display, index)) is not None:
            index += 1
            if (mode.width, mode.height, mode.bits, mode.flags, mode.orientation, mode.fixedOutput) == (
                    current.width, current.height, current.bits, current.flags, current.orientation, current.fixedOutput):
                if 1 < mode.frequency <= maximum:
                    candidates.append(mode.frequency)
        if not candidates:
            raise DisplayError(f"This display has no supported refresh rate at or below {maximum} Hz at its current resolution.")
        # Change only frequency, preserving the current desktop position and orientation.
        target = DEVMODE.from_buffer_copy(current)
        target.frequency = max(candidates)
        target.fields = 0x400000  # DM_DISPLAYFREQUENCY
        current.fields = 0x400000
        return current, target

    def apply(self, display, mode):
        for flags in (2, 0):  # CDS_TEST, then temporary change; never write registry.
            result = self.user.ChangeDisplaySettingsExW(display, c.byref(mode), None, flags, None)
            if result != 0:
                raise DisplayError(f"Windows rejected the display change (code {result}).")

    def reset(self):
        result = self.user.ChangeDisplaySettingsExW(None, None, None, 0, None)
        if result != 0:
            raise DisplayError(f"Windows could not restore saved display settings (code {result}).")
