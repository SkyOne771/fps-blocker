"""Run manually on Windows; --switch briefly changes the foreground display."""
import ctypes
import os
from pathlib import Path
import subprocess
import sys
import time
import tkinter as tk

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fps_blocker.__main__ import App
from fps_blocker.windows import Windows, DEVMODE, MONITORINFO


def main():
    assert os.name == "nt", "Run with Windows Python"
    assert ctypes.sizeof(DEVMODE) == 220
    assert ctypes.sizeof(MONITORINFO) == 104
    windows = Windows()
    foreground = windows.foreground()
    assert foreground is not None, "No foreground display available"
    display = foreground.display
    original, target = windows.limited_mode(display, 60)
    print(f"Display {display}: {original.width}x{original.height}, {original.frequency} Hz; browsing target {target.frequency} Hz", flush=True)

    root = tk.Tk()
    app = App(root, windows)
    root.update()
    try:
        assert root.winfo_height() >= root.winfo_reqheight(), "Window clips its controls"
        print("PASS: GUI opens with all controls visible", flush=True)
    finally:
        app.close()

    if "--switch" not in sys.argv:
        print("Display switching skipped; pass --switch to test it.")
        return
    if original.frequency == target.frequency:
        print("Already at target refresh rate; no lower-rate transition to test.")
        return

    # A second process restores the exact previous refresh rate if this test crashes.
    recovery = (
        "import sys,time,ctypes; sys.path.insert(0,sys.argv[1]); "
        "from fps_blocker.windows import Windows,DEVMODE; time.sleep(10); "
        "mode=DEVMODE.from_buffer_copy(bytes.fromhex(sys.argv[3])); "
        "Windows().apply(sys.argv[2],mode)"
    )
    watchdog = subprocess.Popen([sys.executable, "-c", recovery, str(Path(__file__).resolve().parents[1]), display, bytes(original).hex()])
    restored = False
    try:
        windows.apply(display, target)
        time.sleep(2)
        actual = windows.mode(display)
        assert actual is not None and actual.frequency == target.frequency
        assert (actual.width, actual.height) == (original.width, original.height)
        print(f"PASS: actual display changed to {actual.frequency} Hz; resolution preserved", flush=True)
    finally:
        windows.apply(display, original)
        actual = windows.mode(display)
        restored = actual is not None and actual.frequency == original.frequency
        if restored:
            watchdog.terminate()
            watchdog.wait(timeout=5)
    assert restored, "Restore failed; recovery process will retry"
    print(f"PASS: restored original {actual.frequency} Hz", flush=True)


if __name__ == "__main__":
    main()
