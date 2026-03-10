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
    "EnableShakingLoop": "true",
    "EnableCatchingLoop": "true",
    "EnableReelingLoop": "true",
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
TAB_META = [
    ("home", "🏠", "Home"),
    ("keys", "⌨", "Keys"),
    ("color", "🎨", "Color"),
    ("loadout", "🎣", "Loadout"),
    ("logs", "📜", "Logs"),
]

COLORS = {
    "bg": "#070b12",
    "bg2": "#0b1220",
    "panel": "#101a2b",
    "panel_soft": "#18253a",
    "line": "#2a3f5f",
    "text": "#e4eefc",
    "muted": "#93a8c2",
    "accent": "#65b9ff",
    "accent2": "#2c97ff",
    "success": "#57d8ad",
}


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

    out: list[str] = []
    touched: set[str] = set()
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
        self.title("Fisch Setup Studio")
        self.geometry("860x620")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)

        self.cfg = read_ini()
        self.rods = load_names(RODS_FILE)
        self.enchants = load_names(ENCHANTS_FILE)

        self.tab_frames: dict[str, tk.Frame] = {}
        self.key_entries: dict[str, ttk.Entry] = {}
        self.tab_buttons: dict[str, tk.Button] = {}
        self.active_tab = "home"
        self.enable_shake_var = tk.BooleanVar(value=self._is_enabled(self.cfg.get("EnableShakingLoop", "true")))
        self.enable_catch_var = tk.BooleanVar(value=self._is_enabled(self.cfg.get("EnableCatchingLoop", "true")))
        self.enable_reel_var = tk.BooleanVar(value=self._is_enabled(self.cfg.get("EnableReelingLoop", "true")))

        self._setup_styles()
        self._build_layout()
        self._build_tabs()
        self._build_home()
        self._build_keys()
        self._build_color()
        self._build_loadout()
        self._build_logs()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_tab("home")

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Dark.TEntry",
            fieldbackground=COLORS["bg2"],
            foreground=COLORS["text"],
            bordercolor=COLORS["line"],
            lightcolor=COLORS["line"],
            darkcolor=COLORS["line"],
            insertcolor=COLORS["text"],
            padding=6,
        )
        style.configure(
            "Dark.TCombobox",
            fieldbackground=COLORS["bg2"],
            background=COLORS["bg2"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["accent"],
            bordercolor=COLORS["line"],
            lightcolor=COLORS["line"],
            darkcolor=COLORS["line"],
            padding=4,
        )

    def _label(self, parent: tk.Widget, text: str, *, size: int = 10, bold: bool = False, muted: bool = False) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            bg=parent.cget("bg"),
            fg=COLORS["muted"] if muted else COLORS["text"],
            font=("Segoe UI", size, "bold" if bold else "normal"),
        )

    def _build_layout(self) -> None:
        shell = tk.Frame(self, bg=COLORS["bg"])
        shell.pack(fill="both", expand=True, padx=16, pady=14)

        topbar = tk.Frame(shell, bg=COLORS["panel"], highlightbackground=COLORS["line"], highlightthickness=1)
        topbar.pack(fill="x")

        self._label(topbar, "Fisch Setup Studio", size=18, bold=True).pack(anchor="w", padx=16, pady=(12, 2))
        self._label(topbar, "Dashboard-style setup for keybinds, color config, loadout and logs.", muted=True).pack(
            anchor="w", padx=16, pady=(0, 12)
        )

        self.content = tk.Frame(shell, bg=COLORS["panel"], highlightbackground=COLORS["line"], highlightthickness=1)
        self.content.pack(fill="both", expand=True, pady=(10, 108))

        self.footer = tk.Frame(shell, bg=COLORS["panel"], highlightbackground=COLORS["line"], highlightthickness=1)
        self.footer.place(relx=0, rely=1, relwidth=1, y=-82, height=62)

        self.status = self._label(self.footer, "Ready", muted=True)
        self.status.pack(side="left", padx=14)

        save_btn = tk.Button(
            self.footer,
            text="Save & Finish",
            command=self.save,
            bg=COLORS["accent2"],
            fg="#06111f",
            activebackground=COLORS["accent"],
            activeforeground="#06111f",
            relief="flat",
            padx=14,
            pady=8,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
        )
        save_btn.pack(side="right", padx=14)

        self.nav = tk.Frame(shell, bg=COLORS["panel"], highlightbackground=COLORS["line"], highlightthickness=1)
        self.nav.place(relx=0.5, rely=1, anchor="s", y=-8, width=620, height=58)

    def _build_tabs(self) -> None:
        for tab_name, icon, label in TAB_META:
            btn = tk.Button(
                self.nav,
                text=f"{icon}\n{label}",
                command=lambda t=tab_name: self.show_tab(t),
                relief="flat",
                bd=0,
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                activebackground=COLORS["panel_soft"],
                activeforeground=COLORS["text"],
                font=("Segoe UI", 9, "bold"),
                cursor="hand2",
                width=10,
                height=2,
            )
            btn.pack(side="left", padx=8, pady=6)
            self.tab_buttons[tab_name] = btn

    def _tab_frame(self, key: str) -> tk.Frame:
        frm = tk.Frame(self.content, bg=COLORS["panel"])
        frm.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.tab_frames[key] = frm
        return frm

    def show_tab(self, tab: str) -> None:
        self.active_tab = tab
        self.tab_frames[tab].tkraise()
        for name, btn in self.tab_buttons.items():
            is_active = name == tab
            btn.configure(
                bg=COLORS["panel_soft"] if is_active else COLORS["panel"],
                fg=COLORS["text"] if is_active else COLORS["muted"],
            )

    def on_close(self) -> None:
        self.destroy()

    def _build_home(self) -> None:
        f = self._tab_frame("home")
        self._label(f, "Homescreen", size=14, bold=True).pack(anchor="w", padx=16, pady=(14, 6))
        self._label(f, "Current keybind map", muted=True).pack(anchor="w", padx=16)

        grid = tk.Frame(f, bg=COLORS["panel"])
        grid.pack(fill="x", padx=16, pady=10)

        for idx, (key, label) in enumerate(KEY_FIELDS):
            card = tk.Frame(grid, bg=COLORS["panel_soft"], highlightbackground=COLORS["line"], highlightthickness=1)
            card.grid(row=idx // 3, column=idx % 3, sticky="nsew", padx=6, pady=6)
            self._label(card, label, muted=True).pack(padx=12, pady=(10, 2))
            tk.Label(
                card,
                text=self.cfg.get(key, ""),
                fg=COLORS["success"],
                bg=COLORS["panel_soft"],
                font=("Segoe UI", 12, "bold"),
            ).pack(padx=12, pady=(0, 10))
        for col in range(3):
            grid.grid_columnconfigure(col, weight=1)

    def _build_keys(self) -> None:
        f = self._tab_frame("keys")
        self._label(f, "Keybinds (Fixed)", size=14, bold=True).pack(anchor="w", padx=16, pady=(14, 8))
        self._label(f, "These are no longer configurable.", muted=True).pack(anchor="w", padx=16, pady=(0, 8))
        card = tk.Frame(f, bg=COLORS["panel_soft"], highlightbackground=COLORS["line"], highlightthickness=1)
        card.pack(fill="x", padx=16, pady=6)

        fixed_lines = [
            "F1  → Start Macro",
            "F2  → Pause Macro",
            "F3  → Exit Macro",
            "F4  → Open Feedback",
            "F5  → Reload Macro",
            "F7  → Redo Detection Setup",
            "F12 → Toggle Safe Pause",
        ]
        for line in fixed_lines:
            self._label(card, line).pack(anchor="w", padx=12, pady=4)
    def _build_color(self) -> None:
        f = self._tab_frame("color")
        self._label(f, "Color Config", size=14, bold=True).pack(anchor="w", padx=16, pady=(14, 8))
        row = tk.Frame(f, bg=COLORS["panel"])
        row.pack(fill="x", padx=16)
        self._label(row, "ColorPreset").pack(side="left")
        self.color_entry = ttk.Entry(row, width=34, style="Dark.TEntry")
        self.color_entry.insert(0, self.cfg.get("ColorPreset", "default.ini"))
        self.color_entry.pack(side="left", padx=10)

    def _build_loadout(self) -> None:
        f = self._tab_frame("loadout")
        self._label(f, "Rod, Enchant, Bait", size=14, bold=True).pack(anchor="w", padx=16, pady=(14, 8))
        form = tk.Frame(f, bg=COLORS["panel"])
        form.pack(fill="x", padx=16)

        self.rod_combo = ttk.Combobox(form, values=self.rods, state="readonly", width=32, style="Dark.TCombobox")
        self.enchant_combo = ttk.Combobox(form, values=["None", *self.enchants], state="readonly", width=32, style="Dark.TCombobox")
        self.secondary_combo = ttk.Combobox(form, values=["None", *self.enchants], state="readonly", width=32, style="Dark.TCombobox")
        self.bait_combo = ttk.Combobox(form, values=BAITS, state="readonly", width=32, style="Dark.TCombobox")

        rows = [
            ("Rod", self.rod_combo, self.cfg.get("SelectedRod", "")),
            ("Primary Enchant", self.enchant_combo, self.cfg.get("SelectedEnchant", "None")),
            ("Secondary Enchant", self.secondary_combo, self.cfg.get("SelectedSecondaryEnchant", "None")),
            ("Bait", self.bait_combo, self.cfg.get("SelectedBait", "Worm")),
        ]

        for i, (label, widget, val) in enumerate(rows):
            self._label(form, label).grid(row=i, column=0, sticky="w", pady=8)
            widget.grid(row=i, column=1, sticky="w", padx=12, pady=8)
            if val in widget.cget("values"):
                widget.set(val)
            elif widget.cget("values"):
                widget.current(0)

        toggle_box = tk.Frame(f, bg=COLORS["panel_soft"], highlightbackground=COLORS["line"], highlightthickness=1)
        toggle_box.pack(fill="x", padx=16, pady=(12, 0))
        self._label(toggle_box, "Loop Toggles", size=12, bold=True).pack(anchor="w", padx=10, pady=(8, 4))

        tk.Checkbutton(
            toggle_box,
            text="Enable Shaking Loop",
            variable=self.enable_shake_var,
            bg=COLORS["panel_soft"],
            fg=COLORS["text"],
            activebackground=COLORS["panel_soft"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["bg2"],
        ).pack(anchor="w", padx=10, pady=2)
        tk.Checkbutton(
            toggle_box,
            text="Enable Catching Loop",
            variable=self.enable_catch_var,
            bg=COLORS["panel_soft"],
            fg=COLORS["text"],
            activebackground=COLORS["panel_soft"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["bg2"],
        ).pack(anchor="w", padx=10, pady=2)
        tk.Checkbutton(
            toggle_box,
            text="Enable Cast/Reeling Loop",
            variable=self.enable_reel_var,
            bg=COLORS["panel_soft"],
            fg=COLORS["text"],
            activebackground=COLORS["panel_soft"],
            activeforeground=COLORS["text"],
            selectcolor=COLORS["bg2"],
        ).pack(anchor="w", padx=10, pady=(2, 8))

    def _is_enabled(self, value: str) -> bool:
        text = str(value or "").strip().lower()
        if text == "":
            return True
        return text not in {"0", "false", "off", "no"}

    def _build_logs(self) -> None:
        f = self._tab_frame("logs")
        self._label(f, "Recent Logs", size=14, bold=True).pack(anchor="w", padx=16, pady=(14, 8))
        txt = tk.Text(
            f,
            bg=COLORS["bg2"],
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            wrap="word",
            relief="flat",
            highlightbackground=COLORS["line"],
            highlightthickness=1,
        )
        txt.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        txt.insert("1.0", recent_logs())
        txt.config(state="disabled")

    def save(self) -> None:
        updates = {}
        updates["ColorPreset"] = self.color_entry.get().strip() or "default.ini"
        updates["SelectedRod"] = self.rod_combo.get().strip()
        updates["SelectedEnchant"] = self.enchant_combo.get().strip() or "None"
        updates["SelectedSecondaryEnchant"] = self.secondary_combo.get().strip() or "None"
        updates["SelectedBait"] = self.bait_combo.get().strip() or "Worm"
        updates["EnableShakingLoop"] = "true" if self.enable_shake_var.get() else "false"
        updates["EnableCatchingLoop"] = "true" if self.enable_catch_var.get() else "false"
        updates["EnableReelingLoop"] = "true" if self.enable_reel_var.get() else "false"

        if not updates["SelectedRod"]:
            messagebox.showwarning("Setup", "Please select a rod before finishing setup.")
            return

        write_ini(updates)
        self.status.configure(text="Saved to info.ini. Closing setup...")
        self.saved = True
        self.destroy()


if __name__ == "__main__":
    import sys

    app = SetupApp()
    app.mainloop()
    sys.exit(0 if app.saved else 2)
