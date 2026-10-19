# Contributing

Bug reports, documentation improvements and focused fixes are welcome. For a larger feature, open an issue to discuss its intended behavior first.

## Local setup

1. Clone the repository.
2. Use Python 3.10 or newer. Windows with Tkinter is required for the desktop application; the policy tests can also run on Linux.
3. No third-party Python packages are required.

```powershell
py -3 -m fps_blocker
py -3 -m unittest discover -s tests -v
```

The optional AMD tool requires 64-bit Windows Python and an AMD driver providing the relevant ADL functions. Reading its state is separate from changing it; do not run hardware-changing commands as part of an automated test.

## Before submitting a pull request

- Run `python -m unittest discover -s tests -v` and `git diff --check`.
- For controller or diagnostic changes, cover meaningful state transitions, failures, and restoration behavior with fake adapters.
- For native binding changes, check structure sizes and function signatures on Windows.
- Keep the README accurate about display refresh rate versus GPU-rendered FPS.
- Document hardware checks separately from automated tests. Do not describe an untested panel, driver, or monitor layout as supported by hardware evidence.

`tests/windows_smoke.py` checks native bindings and GUI layout. Adding `--switch` deliberately changes the foreground monitor's refresh rate briefly and restores it; use it only when you intend to test your display.

## Bug reports

Include reproduction steps, expected and actual behavior, Windows/Python versions, monitor model, GPU and driver, resolution, selected limit, and any error message. For brightness flicker, mention whether FreeSync/VRR is enabled and whether the symptom remains with FPS Blocker paused or closed.

Do not commit `freesync-backup.json`, Python caches, or local diagnostic reports containing personal information. Contributions are provided under the repository's MIT license.
