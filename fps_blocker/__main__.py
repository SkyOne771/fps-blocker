import os
import tkinter as tk
from tkinter import ttk, messagebox

from .controller import Controller
from .windows import Windows, DisplayError


BROWSERS = {"Microsoft Edge": "msedge.exe", "Google Chrome": "chrome.exe",
            "Firefox": "firefox.exe", "Brave": "brave.exe", "Opera": "opera.exe",
            "Vivaldi": "vivaldi.exe"}


class App:
    def __init__(self, root, windows):
        self.root = root
        self.controller = Controller(windows)
        self.enabled = tk.BooleanVar(value=False)
        self.rate = tk.StringVar(value="300")
        self.status = tk.StringVar(value="Paused — choose a limit, then enable browsing mode.")
        self.browsers = {name: tk.BooleanVar(value=True) for name in BROWSERS}
        root.title("FPS Blocker · Browsing mode")
        root.geometry("560x650")
        root.minsize(510, 620)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f6fa")
        style.configure("TLabel", background="#f4f6fa", font=("Segoe UI", 10))
        style.configure("TCheckbutton", background="#f4f6fa", font=("Segoe UI", 10))
        frame = ttk.Frame(root, padding=28)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="A quieter browsing mode", font=("Segoe UI", 21, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Windows 10 / 11 · AMD compatible", foreground="#526278").pack(anchor="w", pady=(6, 20))
        ttk.Label(frame, text="Display refresh limit", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.picker = ttk.Combobox(
            frame, textvariable=self.rate,
            values=["24", "30", "40", "48", "50", "60", "75", "90", "100", "120",
                    "144", "165", "180", "200", "240", "280", "300", "360", "480", "500", "540"],
            state="readonly", width=15,
        )
        self.picker.pack(anchor="w", pady=(8, 8))
        ttk.Label(frame, text="Uses the highest supported rate at or below your choice.\nYour resolution stays the same.").pack(anchor="w")
        ttk.Label(frame, text="Apply when these browsers are in front", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(20, 8))
        grid = ttk.Frame(frame)
        grid.pack(fill="x")
        for index, (name, variable) in enumerate(self.browsers.items()):
            ttk.Checkbutton(grid, text=name, variable=variable).grid(row=index // 2, column=index % 2, sticky="w", padx=(0, 30), pady=4)
        ttk.Checkbutton(frame, text="Enable browsing mode", variable=self.enabled, command=self.toggle).pack(anchor="w", pady=(20, 12))
        ttk.Label(frame, textvariable=self.status, wraplength=490, foreground="#245c56").pack(anchor="w")
        ttk.Label(frame, text="Limits displayed frames by changing the browser monitor’s refresh rate.\nThis is not a GPU render-FPS limiter. Other windows on that monitor\nshare the rate. Switching away or closing this app restores it.", foreground="#526278", wraplength=490).pack(anchor="w", pady=(18, 10))
        ttk.Button(frame, text="Restore Windows display settings", command=self.reset).pack(anchor="w")
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.poll()

    def toggle(self):
        self.picker.configure(state="disabled" if self.enabled.get() else "readonly")

    def poll(self):
        try:
            selected = {BROWSERS[name] for name, variable in self.browsers.items() if variable.get()}
            if self.enabled.get() or self.controller.active:
                self.status.set(self.controller.tick(self.enabled.get(), selected, int(self.rate.get())))
        except (DisplayError, OSError) as exc:
            self.enabled.set(False)
            self.toggle()
            try:
                self.controller.restore()
            except (DisplayError, OSError) as restore_error:
                self.status.set(f"{exc} Restore failed: {restore_error}")
            else:
                self.status.set(str(exc))
        self.root.after(750, self.poll)

    def reset(self):
        self.enabled.set(False)
        self.toggle()
        try:
            self.controller.restore()
            self.controller.windows.reset()
            self.status.set("Restored the display settings saved in Windows.")
        except (DisplayError, OSError) as exc:
            messagebox.showerror("Could not restore display", str(exc))

    def close(self):
        try:
            self.controller.restore()
        except (DisplayError, OSError) as exc:
            messagebox.showerror("Could not restore display", f"{exc}\nUse Restore Windows display settings before closing.")
            return
        self.root.destroy()


def main():
    if os.name != "nt":
        raise SystemExit("FPS Blocker requires Windows 10 or 11. Run: py -m fps_blocker")
    root = tk.Tk()
    try:
        windows = Windows()
    except (DisplayError, OSError) as exc:
        messagebox.showerror("FPS Blocker", str(exc))
        root.destroy()
        return
    App(root, windows)
    root.mainloop()


if __name__ == "__main__":
    main()
