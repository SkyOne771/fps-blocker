"""Inspect AMD FreeSync, or run a reversible per-monitor diagnostic change.

API reference: https://gpuopen-librariesandsdks.github.io/adl/display_8h.html
No registry editing or driver installation. Run using Windows Python.
"""
import argparse
import ctypes as c
import json
import os
from pathlib import Path


class Adapter(c.Structure):
    _fields_ = [
        ("size", c.c_int), ("index", c.c_int), ("udid", c.c_char * 256),
        ("bus", c.c_int), ("device", c.c_int), ("function", c.c_int),
        ("vendor", c.c_int), ("name", c.c_char * 256),
        ("display", c.c_char * 256), ("present", c.c_int), ("exists", c.c_int),
        ("driver", c.c_char * 256), ("driver_ext", c.c_char * 256),
        ("pnp", c.c_char * 256), ("os_display", c.c_int),
    ]


class DisplayID(c.Structure):
    _fields_ = [("logical", c.c_int), ("physical", c.c_int),
                ("logical_adapter", c.c_int), ("physical_adapter", c.c_int)]


class Display(c.Structure):
    _fields_ = [("id", DisplayID), ("controller", c.c_int),
                ("name", c.c_char * 256), ("manufacturer", c.c_char * 256),
                ("type", c.c_int), ("output", c.c_int), ("connector", c.c_int),
                ("mask", c.c_int), ("value", c.c_int)]


class ADL:
    def __init__(self):
        if os.name != "nt":
            raise RuntimeError("Use Windows Python for AMD display diagnostics.")
        self.dll = c.CDLL(str(Path(os.environ["SystemRoot"]) / "System32" / "atiadlxx.dll"))
        self.crt = c.CDLL("msvcrt")
        self.crt.malloc.argtypes, self.crt.malloc.restype = [c.c_size_t], c.c_void_p
        self.crt.free.argtypes = [c.c_void_p]
        self.allocations = set()
        callback_type = c.CFUNCTYPE(c.c_void_p, c.c_int)

        def allocate(size):
            pointer = self.crt.malloc(size)
            if pointer:
                self.allocations.add(pointer)
            return pointer

        self.allocate = callback_type(allocate)
        self.context = c.c_void_p()
        self.bind("ADL2_Main_Control_Create", [callback_type, c.c_int, c.POINTER(c.c_void_p)])
        self.bind("ADL2_Main_Control_Destroy", [c.c_void_p])
        self.bind("ADL2_Adapter_NumberOfAdapters_Get", [c.c_void_p, c.POINTER(c.c_int)])
        self.bind("ADL2_Adapter_AdapterInfo_Get", [c.c_void_p, c.POINTER(Adapter), c.c_int])
        self.bind("ADL2_Display_DisplayInfo_Get", [c.c_void_p, c.c_int, c.POINTER(c.c_int), c.POINTER(c.POINTER(Display)), c.c_int])
        self.bind("ADL2_Display_FreeSyncState_Get", [c.c_void_p, c.c_int, c.c_int] + [c.POINTER(c.c_int)] * 4)
        self.bind("ADL2_Display_FreeSyncState_Set", [c.c_void_p, c.c_int, c.c_int, c.c_int, c.c_int])
        self.check(self.dll.ADL2_Main_Control_Create(self.allocate, 1, c.byref(self.context)))

    def bind(self, name, arguments):
        function = getattr(self.dll, name)
        function.argtypes, function.restype = arguments, c.c_int

    @staticmethod
    def check(result):
        if result != 0:
            raise RuntimeError(f"AMD ADL returned error {result}")

    def close(self):
        try:
            self.dll.ADL2_Main_Control_Destroy(self.context)
        finally:
            for pointer in self.allocations:
                self.crt.free(pointer)
            self.allocations.clear()

    def state(self, adapter, display):
        values = [c.c_int() for _ in range(4)]
        self.check(self.dll.ADL2_Display_FreeSyncState_Get(self.context, adapter, display, *(c.byref(value) for value in values)))
        return dict(zip(("current", "default", "min_microhz", "max_microhz"), (value.value for value in values)))

    def displays(self):
        count = c.c_int()
        self.check(self.dll.ADL2_Adapter_NumberOfAdapters_Get(self.context, c.byref(count)))
        if not 0 <= count.value <= 256:
            raise RuntimeError("Invalid AMD adapter count")
        adapters = (Adapter * count.value)()
        for adapter in adapters:
            adapter.size = c.sizeof(Adapter)
        self.check(self.dll.ADL2_Adapter_AdapterInfo_Get(self.context, adapters, c.sizeof(adapters)))
        result = []
        for adapter in adapters:
            if not adapter.present:
                continue
            number, displays = c.c_int(), c.POINTER(Display)()
            status = self.dll.ADL2_Display_DisplayInfo_Get(self.context, adapter.index, c.byref(number), c.byref(displays), 1)
            if status != 0:
                continue
            if not 0 <= number.value <= 256:
                raise RuntimeError("Invalid AMD display count")
            for index in range(number.value):
                display = displays[index]
                # Both connected and mapped; ADL repeats connected physical displays
                # under inactive logical adapters as well.
                if display.value & 3 != 3:
                    continue
                if display.id.logical_adapter != adapter.index:
                    continue
                entry = {"adapter": adapter.index, "display": display.id.logical,
                         "name": display.name.decode("mbcs"),
                         "physical_adapter": display.id.physical_adapter,
                         "physical_display": display.id.physical,
                         "logical_adapter": display.id.logical_adapter,
                         "flags": display.value,
                         "windows_display": adapter.display.decode("mbcs")}
                try:
                    entry.update(self.state(adapter.index, display.id.logical))
                except RuntimeError as error:
                    entry["error"] = str(error)
                result.append(entry)
        return result

    def set(self, entry, value):
        self.check(self.dll.ADL2_Display_FreeSyncState_Set(self.context, entry["adapter"], entry["display"], value, 0))
        actual = self.state(entry["adapter"], entry["display"])
        if actual["current"] != value:
            raise RuntimeError(f"FreeSync readback does not match: {actual}")
        return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disable", action="store_true")
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--monitor", default="AORUS FO32U2P")
    parser.add_argument("--backup", type=Path, default=Path(__file__).resolve().parent.parent / "freesync-backup.json")
    args = parser.parse_args()
    if args.disable and args.restore:
        parser.error("Choose either --disable or --restore")
    adl = ADL()
    try:
        displays = adl.displays()
        print(json.dumps(displays, indent=2), flush=True)
        if not (args.disable or args.restore):
            return
        matches = [entry for entry in displays if entry["name"].casefold() == args.monitor.casefold() and "current" in entry]
        if len(matches) != 1:
            raise RuntimeError("Expected exactly one matching FreeSync display; no change made.")
        entry = matches[0]
        if args.restore:
            saved = json.loads(args.backup.read_text(encoding="utf-8"))
            if saved["name"] != entry["name"] or saved["windows_display"] != entry["windows_display"]:
                raise RuntimeError("Backup belongs to a different display; no change made.")
            target = saved["current"]
        else:
            if entry["current"] == 0:
                print("FreeSync is already disabled; no change made.")
                return
            # Never overwrite the original saved setting on repeated runs.
            with args.backup.open("x", encoding="utf-8") as file:
                json.dump(entry, file, indent=2)
            target = 0
        try:
            actual = adl.set(entry, target)
        except Exception:
            adl.set(entry, entry["current"])
            raise
        print("Verified FreeSync setting:", actual, flush=True)
        print("Temporary driver setting; no reboot persistence requested.")
    finally:
        adl.close()


if __name__ == "__main__":
    main()
