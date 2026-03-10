#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

ROOT = Path(__file__).resolve().parent
INFO_INI = ROOT / "info.ini"
RODS_FILE = ROOT / "server-dashboard" / "data" / "rods.json"
ENCHANTS_FILE = ROOT / "server-dashboard" / "data" / "enchants.json"
LOG_FILE = ROOT / "logs" / "macro.log"

DEFAULTS = {
    "HotkeyStart": "F1",
    "HotkeyPause": "F2",
    "HotkeyExit": "F3",
    "HotkeyFeedback": "F4",
    "HotkeyReload": "F5",
    "HotkeyRedo": "F7",
    "HotkeySafePause": "F12",
    "ColorPreset": "default.ini",
    "SelectedRod": "",
    "SelectedEnchant": "None",
    "SelectedSecondaryEnchant": "None",
    "SelectedBait": "Worm",
}
BAITS = ["Worm", "Insect", "Minnow", "Shrimp", "Bagel", "Seaweed", "None"]
KEY_FIELDS = [
    ("HotkeyStart", "Start"),
    ("HotkeyPause", "Pause"),
    ("HotkeyExit", "Exit"),
    ("HotkeyFeedback", "Feedback"),
    ("HotkeyReload", "Reload"),
    ("HotkeyRedo", "Redo Setup"),
    ("HotkeySafePause", "Safe Pause"),
]


def read_ini() -> dict[str, str]:
    data = dict(DEFAULTS)
    if not INFO_INI.exists():
        return data
    for raw in INFO_INI.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip().lstrip("\ufeff")
        if not line or line.startswith((";", "#", "[")) or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip():
            data[k.strip()] = v.strip()
    return data


def write_ini(updates: dict[str, str]) -> None:
    existing = []
    if INFO_INI.exists():
        existing = INFO_INI.read_text(encoding="utf-8", errors="ignore").splitlines()

    merged = read_ini()
    merged.update(updates)

    if not existing:
        INFO_INI.write_text("\n".join(f"{k}={merged.get(k,'')}" for k in DEFAULTS) + "\n", encoding="utf-8")
        return

    out = []
    touched = set()
    for raw in existing:
        line = raw.strip().lstrip("\ufeff")
        if not line or line.startswith((";", "#", "[")) or "=" not in line:
            out.append(raw)
            continue
        k, _ = line.split("=", 1)
        key = k.strip()
        if key in merged:
            out.append(f"{key}={merged[key]}")
            touched.add(key)
        else:
            out.append(raw)

    for key, value in merged.items():
        if key not in touched:
            out.append(f"{key}={value}")

    INFO_INI.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def load_names(path: Path, name_key: str = "name") -> list[str]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    names = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and str(item.get(name_key, "")).strip():
                names.append(str(item[name_key]).strip())
    return sorted(set(names), key=str.lower)


def recent_logs() -> str:
    if not LOG_FILE.exists():
        return "No log file available yet."
    lines = [x for x in LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines() if x.strip()]
    return "\n".join(lines[-60:]) if lines else "Log file is empty."


class SetupApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.saved = False
        self.title("Fisch Mode - Python Setup")
        self.geometry("760x560")
        self.configure(bg="#0b1220")
        self.resizable(False, False)

        self.cfg = read_ini()
        self.rods = load_names(RODS_FILE)
        self.enchants = load_names(ENCHANTS_FILE)

        self.tab_frames: dict[str, tk.Frame] = {}
        self.key_entries: dict[str, ttk.Entry] = {}

        shell = tk.Frame(self, bg="#0b1220")
        shell.pack(fill="both", expand=True, padx=14, pady=12)

        title = tk.Label(shell, text="Fisch Setup", font=("Segoe UI", 18, "bold"), fg="#dbeafe", bg="#0b1220")
        title.pack(anchor="w")

        self.content = tk.Frame(shell, bg="#101a2b", highlightbackground="#243b5c", highlightthickness=1)
        self.content.pack(fill="both", expand=True, pady=(8, 76))

        for tab in ("home", "keys", "color", "loadout", "logs"):
            frm = tk.Frame(self.content, bg="#101a2b")
            self.tab_frames[tab] = frm
            frm.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._build_home()
        self._build_keys()
        self._build_color()
        self._build_loadout()
        self._build_logs()

        bottom = tk.Frame(shell, bg="#0f172a")
        bottom.place(relx=0, rely=1, relwidth=1, y=-62, height=56)
        ttk.Button(bottom, text="Save & Finish", command=self.save).pack(side="right", padx=12, pady=10)

        nav = tk.Frame(shell, bg="#0f172a", highlightbackground="#243b5c", highlightthickness=1)
        nav.place(relx=0.5, rely=1, anchor="s", y=-4, width=540, height=48)
        tabs = [("🏠", "home"), ("⌨", "keys"), ("🎨", "color"), ("🎣", "loadout"), ("📜", "logs")]
        for icon, tab in tabs:
            ttk.Button(nav, text=icon, width=6, command=lambda t=tab: self.show_tab(t)).pack(side="left", padx=8, pady=8)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_tab("home")

    def on_close(self) -> None:
        self.destroy()

    def show_tab(self, tab: str) -> None:
        self.tab_frames[tab].tkraise()

    def _build_home(self) -> None:
        f = self.tab_frames["home"]
        tk.Label(f, text="Homescreen", font=("Segoe UI", 14, "bold"), fg="#dbeafe", bg="#101a2b").pack(anchor="w", padx=16, pady=(14, 6))
        tk.Label(f, text="Current keybinds", fg="#93a8c2", bg="#101a2b").pack(anchor="w", padx=16)
        grid = tk.Frame(f, bg="#101a2b")
        grid.pack(fill="x", padx=16, pady=10)
        for idx, (key, label) in enumerate(KEY_FIELDS):
            card = tk.Frame(grid, bg="#18253a", highlightbackground="#2a3f5f", highlightthickness=1)
            card.grid(row=idx // 3, column=idx % 3, sticky="nsew", padx=6, pady=6)
            tk.Label(card, text=label, fg="#9fb7d9", bg="#18253a").pack(padx=12, pady=(10, 2))
            tk.Label(card, text=self.cfg.get(key, ""), fg="#e2e8f0", bg="#18253a", font=("Segoe UI", 11, "bold")).pack(padx=12, pady=(0, 10))
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1)

    def _build_keys(self) -> None:
        f = self.tab_frames["keys"]
        tk.Label(f, text="Keybinds", font=("Segoe UI", 14, "bold"), fg="#dbeafe", bg="#101a2b").pack(anchor="w", padx=16, pady=(14, 8))
        form = tk.Frame(f, bg="#101a2b")
        form.pack(fill="x", padx=16)
        for r, (key, label) in enumerate(KEY_FIELDS):
            tk.Label(form, text=label, fg="#cbd5e1", bg="#101a2b").grid(row=r, column=0, sticky="w", pady=5)
            e = ttk.Entry(form, width=18)
            e.insert(0, self.cfg.get(key, ""))
            e.grid(row=r, column=1, sticky="w", padx=10, pady=5)
            self.key_entries[key] = e

    def _build_color(self) -> None:
        f = self.tab_frames["color"]
        tk.Label(f, text="Color Config", font=("Segoe UI", 14, "bold"), fg="#dbeafe", bg="#101a2b").pack(anchor="w", padx=16, pady=(14, 8))
        row = tk.Frame(f, bg="#101a2b")
        row.pack(fill="x", padx=16)
        tk.Label(row, text="ColorPreset", fg="#cbd5e1", bg="#101a2b").pack(side="left")
        self.color_entry = ttk.Entry(row, width=32)
        self.color_entry.insert(0, self.cfg.get("ColorPreset", "default.ini"))
        self.color_entry.pack(side="left", padx=10)

    def _build_loadout(self) -> None:
        f = self.tab_frames["loadout"]
        tk.Label(f, text="Rod, Enchant, Bait", font=("Segoe UI", 14, "bold"), fg="#dbeafe", bg="#101a2b").pack(anchor="w", padx=16, pady=(14, 8))
        form = tk.Frame(f, bg="#101a2b")
        form.pack(fill="x", padx=16)

        self.rod_combo = ttk.Combobox(form, values=self.rods, state="readonly", width=30)
        self.enchant_combo = ttk.Combobox(form, values=["None", *self.enchants], state="readonly", width=30)
        self.secondary_combo = ttk.Combobox(form, values=["None", *self.enchants], state="readonly", width=30)
        self.bait_combo = ttk.Combobox(form, values=BAITS, state="readonly", width=30)

        rows = [
            ("Rod", self.rod_combo, self.cfg.get("SelectedRod", "")),
            ("Primary Enchant", self.enchant_combo, self.cfg.get("SelectedEnchant", "None")),
            ("Secondary Enchant", self.secondary_combo, self.cfg.get("SelectedSecondaryEnchant", "None")),
            ("Bait", self.bait_combo, self.cfg.get("SelectedBait", "Worm")),
        ]
        for i, (label, widget, val) in enumerate(rows):
            tk.Label(form, text=label, fg="#cbd5e1", bg="#101a2b").grid(row=i, column=0, sticky="w", pady=6)
            widget.grid(row=i, column=1, sticky="w", padx=10, pady=6)
            if val in widget.cget("values"):
                widget.set(val)
            elif widget.cget("values"):
                widget.current(0)

    def _build_logs(self) -> None:
        f = self.tab_frames["logs"]
        tk.Label(f, text="Recent Logs", font=("Segoe UI", 14, "bold"), fg="#dbeafe", bg="#101a2b").pack(anchor="w", padx=16, pady=(14, 8))
        txt = tk.Text(f, bg="#0b1220", fg="#cbd5e1", insertbackground="#cbd5e1", wrap="word")
        txt.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        txt.insert("1.0", recent_logs())
        txt.config(state="disabled")

    def save(self) -> None:
        updates = {k: v.get().strip() for k, v in self.key_entries.items()}
        updates["ColorPreset"] = self.color_entry.get().strip() or "default.ini"
        updates["SelectedRod"] = self.rod_combo.get().strip()
        updates["SelectedEnchant"] = self.enchant_combo.get().strip() or "None"
        updates["SelectedSecondaryEnchant"] = self.secondary_combo.get().strip() or "None"
        updates["SelectedBait"] = self.bait_combo.get().strip() or "Worm"

        if not updates["SelectedRod"]:
            messagebox.showwarning("Setup", "Please select a rod before finishing setup.")
            return

        write_ini(updates)
        self.saved = True
        self.destroy()


if __name__ == "__main__":
    import sys
    app = SetupApp()
    app.mainloop()
    sys.exit(0 if app.saved else 2)
