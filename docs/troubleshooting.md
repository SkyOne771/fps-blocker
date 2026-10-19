# Troubleshooting and recovery

## The app will not start

Use Windows Python 3.10 or newer with Tcl/Tk installed. From the repository root, run `py -3 -m fps_blocker` in a terminal to see errors. If `py.exe` is not on PATH, `start.bat` also searches the standard per-user Python installation directory before trying `python`.

The GUI and Win32 operations require Windows. The policy unit tests can run on Linux, but that does not exercise a physical Windows display.

## Selecting 300 does not produce 300 Hz

The number is a maximum refresh-rate limit. The app selects an existing supported mode and does not overclock the display. A 240 Hz monitor remains at 240 Hz when the limit is 300. A lower-rate monitor is never raised by the app.

## No supported mode at the selected rate

Choose a higher limit. The app only considers modes matching the current resolution, color depth, orientation, display flags and fixed-output setting. For example, a display may support 60 Hz at its current resolution but not 30 Hz. Unsupported requests cause the app to pause instead of forcing a custom mode.

## The monitor briefly goes black when switching apps

A monitor can blank while switching display modes. Pause browsing mode to compare behavior without automatic switching. The app polls every 750 ms, so a focus change can take that long to trigger restoration, plus the time the display takes to change modes.

## Refresh rate stayed low after a crash

Reopen the app and use **Restore Windows display settings**, or select your preferred rate in Windows Settings → System → Display → Advanced display.

The app's recovery button resets all displays to the configuration saved in Windows. It does not load an AMD FreeSync backup.

## Brightness flicker on dark OLED surfaces

The local investigation involved an RX 7900 XTX and AORUS FO32U2P OLED. FPS Blocker was closed, and Windows reported a steady 4K/240 Hz mode. ADL reported FreeSync enabled for desktop, video and gaming. After FreeSync was disabled, the user reported that the flicker stopped; Windows still reported 4K/240 Hz.

That finding points to VRR-related flicker on the tested setup. It does not establish the cause of every monitor's flicker, and desktop screenshots cannot confirm physical panel brightness changes.

Inspect AMD driver state without changing it:

```powershell
py -3 tools/amd_freesync.py
```

For a reversible comparison on an exactly named supported monitor:

```powershell
py -3 tools/amd_freesync.py --monitor "AORUS FO32U2P" --disable
# Observe the same scene, then restore if needed:
py -3 tools/amd_freesync.py --monitor "AORUS FO32U2P" --restore
```

Disabling FreeSync removes variable refresh for that monitor. The diagnostic tool does not force a different nominal refresh rate. It verifies driver state, but whether a visible symptom improves must be checked on the physical screen.

No persistence flush is requested. If the setting resets after reboot, use AMD Software or the monitor's own FreeSync control to manage it persistently.

## An existing FreeSync backup blocks another change

This prevents an original setting from being overwritten. Restore it first if that is the intended action. If you deliberately want to establish a different baseline, archive the previous backup elsewhere before starting another diagnostic change. Keep the old file if you may need its setting later.

Restore requires the same display name and Windows display identity. A monitor reconnection or topology change can cause this check to reject the backup; inspect the current output and adjust FreeSync through AMD Software rather than bypassing the check blindly.

## Reporting a problem

Open a GitHub issue with Windows and Python versions, GPU/driver and monitor model, the chosen refresh limit, current resolution/rate, steps to reproduce, and the error message. Mention whether pausing the utility changes the symptom. Avoid posting a complete hardware diagnostic dump or your backup file when a short description will do.
