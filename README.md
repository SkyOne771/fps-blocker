<img src="assets/icon.svg" width="64" height="64" alt="">

# fps blocker

A small Windows 10/11 utility that lowers the browser monitor's refresh rate while
a selected browser is in front. Works independently of the GPU vendor, including
AMD. Switching away, pausing, or closing the app restores the original rate.

**This is a display refresh limiter, not a strict GPU render-FPS limiter.** A 60 Hz
display shows at most 60 refreshes per second; an application can still render
more frames internally. Video decoding is not capped. Other windows on the same
monitor share its refresh rate. Windows may briefly blank the screen when changing
modes. Only rates reported as supported at the current resolution are used.

### Run

1. Install Python 3.10 or newer on Windows, including Tcl/Tk and the Python launcher.
2. Double-click `start.bat`, or run `py -3 -m fps_blocker` from this folder.
3. Choose a refresh limit (300 Hz is selected by default), select your browsers, and enable
   browsing mode. Keep the utility running, then switch to your browser.

The utility uses the highest supported refresh rate at or below your choice. If
you select 300 Hz on a 240 Hz display, it stays at 240 Hz; selecting a higher
limit does not increase your monitor's refresh rate. Presets range from 24 to
540 Hz, including 144, 165, 180, 240, 280, 300, and 360 Hz. If
your display does not support one, it reports that and pauses. It never increases
an already lower refresh rate. Chrome, Edge, Firefox, Brave, Opera, and Vivaldi
are supported. On multiple monitors, it changes the monitor containing most of the
foreground browser window and restores the previous monitor when you move away.

No external Python packages, administrator privileges, browser extensions, or
driver profile changes are required. Changes are temporary and are not saved to
Windows display configuration. After a forced termination, reopen the app and
click **Restore Windows display settings**, or use Windows Settings → System →
Display → Advanced display to select your preferred refresh rate. The restore
button resets all displays to the configuration saved in Windows.

### AMD and strict FPS caps

AMD Radeon Chill is documented for supported games and graphics APIs; this app
does not claim it can enforce a driver-level cap in every browser. If you need a
strict cap on GPU rendering rather than displayed refreshes, this implementation
does not provide one.

References: [Windows display mode API](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-changedisplaysettingsexw),
[AMD Radeon Chill compatibility](https://www.amd.com/en/products/software/adrenalin/radeon-software-chill.html).

### Development

Run `python -m unittest discover -s tests -v`. The tests cover browser focus,
monitor handoff, pause/restore, unsupported rates, and failed display changes.
GitHub Actions also checks Win32 structure sizes and API binding on Windows.
Run `py -3 tests/windows_smoke.py` to check the Windows API bindings and GUI, or
add `--switch` to briefly test a real refresh change with automatic restoration
and a separate recovery process. A local hardware run passed at 3840×2160,
switching from 240 Hz to 60 Hz and restoring 240 Hz.
Polling runs every 750 ms, so restoration is not instantaneous. HDR, VRR,
remote desktops, and dynamic refresh rate configurations need hardware validation.

### Dark-area flicker investigation

On the local RX 7900 XTX / AORUS FO32U2P system, the app was closed and 40
display-mode samples all reported 3840×2160 at 240 Hz with no mode transitions.
AMD's ADL API reported FreeSync enabled for static desktop, video, and gaming,
with a 48–240 Hz range. This makes VRR a candidate for dark-area brightness
flicker; it does not confirm the physical cause.

`tools/amd_freesync.py` reads the driver's FreeSync state. With `--disable`, it
backs up the original state to `freesync-backup.json`, disables FreeSync on the
exactly named AORUS FO32U2P display, and verifies the driver's readback. It does
not change display resolution or the nominal refresh rate. No driver-settings
flush is requested, so reboot persistence is not guaranteed. Other monitor
models can be selected with `--monitor "Exact display name"`.

Double-click `restore-freesync.bat` to restore the saved FreeSync setting. The
backup is intentionally never overwritten by another disable operation. Restore
requires the same display name and Windows display identity. A real test has
verified the change from FreeSync mask 7 (all three uses) to 0 (off); whether
visible flicker improves still requires observation of the physical screen.

API reference: [AMD ADL FreeSync APIs](https://gpuopen-librariesandsdks.github.io/adl/display_8h.html).
