# Architecture

FPS Blocker separates the desktop interface, the foreground-window policy, and the native display APIs. This lets most behavior be tested without changing a developer's monitor settings.

## Components

| Component | Responsibility |
| --- | --- |
| `fps_blocker/__main__.py` | Tkinter controls, browser selection, 750 ms polling, status messages, shutdown |
| `fps_blocker/controller.py` | Decide when to limit a monitor and when to restore its original mode |
| `fps_blocker/windows.py` | Win32 foreground-process lookup, monitor detection, mode enumeration, test/apply/reset |
| `tools/amd_freesync.py` | Optional AMD ADL enumeration, FreeSync inspection, backup, change, readback and restoration |
| `tools/check_docs_sync.py` | CI code/docs change policy and validation of local Markdown links and HTML image targets |
| `tests/test_controller.py` | Focus, monitor handoff, unsupported rates, failed changes and restoration retries |
| `tests/test_amd_freesync.py` | Backup preservation, restoration identity checks, no-op behavior and rollback |
| `tests/windows_smoke.py` | Manual native binding, GUI layout and optional physical display checks |

## Foreground browser flow

1. `GetForegroundWindow` identifies the foreground window.
2. `GetWindowThreadProcessId` and `QueryFullProcessImageNameW` resolve its executable.
3. `MonitorFromWindow` and `GetMonitorInfoW` identify the monitor containing the largest portion of that window.
4. The controller compares the executable with the selected browser names.
5. `EnumDisplaySettingsW` enumerates modes matching the current resolution, color depth, display flags, orientation and fixed-output setting.
6. The highest supported frequency at or below the chosen maximum is selected. A monitor already running at a lower rate is left alone.
7. `ChangeDisplaySettingsExW` tests the frequency change before applying it. The change uses `DM_DISPLAYFREQUENCY` and does not write the display configuration to the registry.
8. When the browser loses focus, moves to another monitor, or browsing mode is disabled, the controller restores the previous frequency.

Only one foreground browser monitor is limited at a time. Focus switching can produce a display mode change; there is currently no focus debounce or tray integration.

## Failure handling

The controller remembers the original mode only after a successful apply. If restoring fails, it retains that mode so a later call can retry. The interface pauses on display errors, attempts restoration, and presents the error to the user. Normal shutdown refuses to close if restoring the active monitor fails.

The recovery button asks Windows to restore its saved display configuration for all displays. That is a recovery path after abnormal termination, not a FreeSync restore operation.

## AMD diagnostic flow

ADL exposes the same connected physical display through several logical adapters. The diagnostic tool filters for the owning logical adapter and requires exactly one display with the requested name and readable FreeSync state.

Before disabling FreeSync, it creates the backup with exclusive file creation so an earlier backup cannot be replaced accidentally. After setting a value, it reads the driver state again. A failed set or mismatched readback triggers an attempt to restore the value observed before the operation. Restore checks the monitor name and Windows display identity against the backup.

The tool does not request `ADL_Flush_Driver_Data`, so it makes no guarantee that a change survives a reboot. It runs separately from the GUI and never automatically changes VRR on browser focus.

## Design decisions

- **Python standard library:** Tkinter provides a small native desktop interface; `ctypes` avoids shipping vendor SDK binaries or requiring additional Python packages.
- **Display refresh control:** the main utility uses supported Windows APIs across GPU vendors. It does not inject into browser processes or claim a GPU rendering cap.
- **Separate optional vendor tool:** AMD-specific behavior does not prevent the main utility from running on another GPU.
- **Hardware adapter boundary:** tests exercise state transitions and failure recovery using fakes; physical checks remain explicit manual operations.

## Validation

The automated suite covers controller, FreeSync diagnostic, and documentation-check behavior. Windows CI also checks that `DEVMODE` is 220 bytes, `MONITORINFO` is 104 bytes, and the Win32 adapter binds successfully.

A separate **Documentation sync** CI job compares the pushed commit range, or
the pull request's base with the checked-out head. Changes to application Python,
tool Python, root batch launchers, or CI workflows require an accompanying README
or technical-doc update. The job also validates local documentation link/image
targets. This detects omitted docs and broken paths, not semantic inaccuracies;
documentation still needs human or agent review alongside the implementation.

Observed local results:

- Windows Python 3.13 launched and closed the Tkinter interface, with all controls visible.
- A physical 3840×2160 display changed from 240 Hz to 60 Hz and restored 240 Hz. Resolution remained unchanged.
- The 300 Hz preset selected 240 Hz on the tested 240 Hz display.
- During the flicker investigation, 40 Windows display-mode samples reported a constant 240 Hz while FPS Blocker was closed.
- AMD ADL reported FreeSync state mask 7 before the change and 0 afterward. The user reported that dark-area flicker stopped.

The FreeSync result supports VRR as the cause on that tested system; it is not a controlled comparison across panels or drivers. Physical browser-focus handoff has not been independently validated end to end; its policy is covered by unit tests. No power consumption, temperature, latency, or rendering-FPS benchmarks have been recorded.
