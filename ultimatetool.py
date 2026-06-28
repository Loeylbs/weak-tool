#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  ██████╗ ██████╗ ██╗███╗   ███╗███████╗
  ██╔══██╗██╔══██╗██║████╗ ████║██╔════╝
  ██████╔╝██████╔╝██║██╔████╔██║█████╗
  ██╔═══╝ ██╔══██╗██║██║╚██╔╝██║██╔══╝
  ██║     ██║  ██║██║██║ ╚═╝ ██║███████╗
  ╚═╝     ╚═╝  ╚═╝╚═╝╚═╝     ╚═╝╚══════╝

  PRIME TOOL v4.1.0 — Multi-Tool Terminal UPGRADED
  Nouveautés v4.1.0 : Firewall Rules, SSH Audit, Watcher Logs,
    Services Manager, Env Inspector, ARP Table, Net Connections,
    File Hasher, Cron Inspector.
"""

import os
import sys
import socket
import platform
import time
import hashlib
import base64
import random
import string
import getpass
import shutil
import subprocess
import urllib.request
import urllib.parse
import json
import concurrent.futures
from datetime import datetime
from collections import deque

# ── AUTO-INSTALL ──────────────────────────────────────────
def _ensure(*pkgs):
    for p in pkgs:
        try:
            __import__(p)
        except ImportError:
            print(f"  [*] Installation de {p}...")
            subprocess.run([sys.executable, "-m", "pip", "install", p, "-q"],
                           capture_output=True)

_ensure("rich", "psutil", "pyfiglet")

from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich.text    import Text
from rich.rule    import Rule
from rich.align   import Align
from rich         import box
import psutil
import pyfiglet

console = Console(width=shutil.get_terminal_size().columns)

# ── CONFIG ───────────────────────────────────────────────
TOOL_NAME    = "PRIME"
VERSION      = "v4.1.0"
LANG         = "fr"
CMD_HISTORY  = deque(maxlen=20)

# ── THÈMES ───────────────────────────────────────────────
THEMES = {
    "cyber": {
        "name": "Cyber", "primary": "bright_cyan", "secondary": "blue",
        "accent": "bright_white", "danger": "red", "success": "green",
        "warning": "yellow", "dim_col": "bright_black", "border": "cyan",
        "cat_sys": "yellow", "cat_net": "green", "cat_mon": "cyan",
        "cat_uti": "magenta", "cat_adv": "bright_blue",
        "dots": "·  · · ·  · ·  · · ·  ·  · · ·  · ·  · · ·  ·  · · ·  · ·  · · ·  ·",
        "box": box.SQUARE,
    },
    "matrix": {
        "name": "Matrix", "primary": "bright_green", "secondary": "green",
        "accent": "bright_white", "danger": "bright_red", "success": "bright_green",
        "warning": "yellow", "dim_col": "dark_green", "border": "green",
        "cat_sys": "bright_green", "cat_net": "green", "cat_mon": "bright_green",
        "cat_uti": "green", "cat_adv": "bright_green",
        "dots": "0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 0",
        "box": box.SIMPLE,
    },
    "blood": {
        "name": "Blood", "primary": "bright_red", "secondary": "red",
        "accent": "white", "danger": "bright_red", "success": "bright_red",
        "warning": "red", "dim_col": "bright_black", "border": "red",
        "cat_sys": "bright_red", "cat_net": "red", "cat_mon": "bright_red",
        "cat_uti": "red", "cat_adv": "bright_red",
        "dots": "▓ ░ ▓ ▓ ░ ▒ ▓ ░ ▒ ▓ ▓ ░ ▓ ▒ ░ ▓ ▓ ░ ▒ ▓ ░ ▒ ▓ ▓ ░ ▓ ▒ ░ ▓ ▓ ░ ▒",
        "box": box.HEAVY,
    },
    "ghost": {
        "name": "Ghost", "primary": "white", "secondary": "bright_white",
        "accent": "bright_white", "danger": "red", "success": "white",
        "warning": "bright_white", "dim_col": "bright_black", "border": "white",
        "cat_sys": "white", "cat_net": "bright_white", "cat_mon": "white",
        "cat_uti": "bright_white", "cat_adv": "white",
        "dots": "  ·   ·  ·   ·   ·  ·   ·  ·   ·   ·  ·   ·  ·   ·   ·  ·   ·  ·",
        "box": box.MINIMAL,
    },
}
THEME_NAMES = list(THEMES.keys())
CURRENT_THEME_IDX = 0

def th():
    return THEMES[THEME_NAMES[CURRENT_THEME_IDX]]

# ── TRADUCTIONS ──────────────────────────────────────────
def t(key: str) -> str:
    TEXTS = {
        "fr": {
            "c_sys": "SYSTÈME", "c_net": "RÉSEAU", "c_mon": "MONITORING",
            "c_uti": "UTILITAIRES", "c_adv": "AVANCÉ", "c_new": "NOUVEAU v4.1",
            "sys1": "Info Système", "sys2": "Statut CPU", "sys3": "Info RAM",
            "sys4": "Info Disque", "sys5": "Uptime / Boot", "sys6": "Exporter Rapport",
            "net1": "Info Réseau", "net2": "Test Ping", "net3": "Stats Réseau",
            "net4": "Lookup DNS", "net5": "Check Ports", "net6": "Scan LAN",
            "mon1": "Moniteur Live", "mon2": "Top Processus",
            "uti1": "Hash Generator", "uti2": "Générateur Mdp", "uti3": "Testeur Mdp",
            "uti4": "Outil Base64", "uti5": "Nettoyer Temp",
            "adv1": "Traceroute", "adv2": "Whois / GeoIP", "adv3": "QR Code ASCII",
            "adv4": "Convertisseur", "adv5": "Proc. Suspects", "adv6": "Speedtest",
            # ── NOUVELLES FEATURES ──
            "new1": "Firewall Rules",   "new2": "SSH Audit",
            "new3": "Watcher Logs",     "new4": "Services Manager",
            "new5": "Env Inspector",    "new6": "ARP Table",
            "new7": "Net Connections",  "new8": "File Hasher",
            "new9": "Cron Inspector",
            # ───────────────────────
            "theme": "Changer Thème", "hist": "Historique", "lang": "Langue (FR/EN)",
            "quit": "[ QUITTER ]", "prompt": "  ❯ ", "bye": "À plus !",
            "err": "Choix invalide.", "pause": "  ↵ Entrée pour continuer..."
        },
        "en": {
            "c_sys": "SYSTEM", "c_net": "NETWORK", "c_mon": "MONITORING",
            "c_uti": "UTILITIES", "c_adv": "ADVANCED", "c_new": "NEW v4.1",
            "sys1": "System Info", "sys2": "CPU Status", "sys3": "RAM Info",
            "sys4": "Disk Info", "sys5": "Uptime / Boot", "sys6": "Export Report",
            "net1": "Network Info", "net2": "Ping Test", "net3": "Net Stats",
            "net4": "DNS Lookup", "net5": "Port Checker", "net6": "LAN Scanner",
            "mon1": "Live Monitor", "mon2": "Top Processes",
            "uti1": "Hash Generator", "uti2": "Password Gen", "uti3": "Pass Checker",
            "uti4": "Base64 Tool", "uti5": "Clean Temp",
            "adv1": "Traceroute", "adv2": "Whois / GeoIP", "adv3": "ASCII QR Code",
            "adv4": "Converter", "adv5": "Susp. Procs", "adv6": "Speedtest",
            "new1": "Firewall Rules",   "new2": "SSH Audit",
            "new3": "Log Watcher",      "new4": "Services Manager",
            "new5": "Env Inspector",    "new6": "ARP Table",
            "new7": "Net Connections",  "new8": "File Hasher",
            "new9": "Cron Inspector",
            "theme": "Change Theme", "hist": "History", "lang": "Language (EN/FR)",
            "quit": "[ QUIT ]", "prompt": "  ❯ ", "bye": "See ya!",
            "err": "Invalid choice.", "pause": "  ↵ Press Enter to continue..."
        }
    }
    return TEXTS[LANG].get(key, key)

# ── HELPERS ──────────────────────────────────────────────
def clr():
    os.system("cls" if os.name == "nt" else "clear")

def pct_bar(pct, width=16, theme_colors=True):
    filled = max(0, int(pct / 100 * width))
    if theme_colors and THEME_NAMES[CURRENT_THEME_IDX] in ("matrix", "blood"):
        p   = th()["primary"]
        dim = th()["dim_col"]
        return f"[{p}]{'█'*filled}[/{p}][{dim}]{'░'*(width-filled)}[/{dim}]"
    color = "green" if pct < 60 else "yellow" if pct < 85 else "red"
    return f"[{color}]{'█'*filled}{'░'*(width-filled)}[/{color}]"

def pause():
    console.print()
    console.input(f"[dim]{t('pause')}[/dim]")

def is_admin():
    try:
        return os.getuid() == 0
    except AttributeError:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def themed_table(*args, **kwargs):
    kwargs.setdefault("box", th()["box"])
    kwargs.setdefault("border_style", th()["border"])
    return Table(*args, **kwargs)

def success(msg):
    console.print(f"  [{th()['success']}]✔ {msg}[/{th()['success']}]")

def error(msg):
    console.print(f"  [{th()['danger']}]✘ {msg}[/{th()['danger']}]")

def info(msg):
    console.print(f"  [{th()['secondary']}]ℹ {msg}[/{th()['secondary']}]")

def warn(msg):
    console.print(f"  [{th()['warning']}]⚠ {msg}[/{th()['warning']}]")

# ── DÉCOR / BANNER ───────────────────────────────────────
def _gradient_banner(ascii_logo: str):
    theme_key = THEME_NAMES[CURRENT_THEME_IDX]
    lines = ascii_logo.rstrip().splitlines()
    width = shutil.get_terminal_size().columns

    if theme_key == "cyber":
        gradient = ["bright_cyan","cyan","blue","bright_blue","cyan","bright_cyan"]
    elif theme_key == "matrix":
        gradient = ["bright_green","green","bright_green","green","bright_green","green"]
    elif theme_key == "blood":
        gradient = ["bright_red","red","bright_red","red","bright_red","bright_red"]
    else:
        gradient = ["white","bright_white","white","bright_white","white","white"]

    for i, line in enumerate(lines):
        color = gradient[i % len(gradient)]
        console.print(f"[bold {color}]{line.center(width)}[/bold {color}]")

def banner():
    clr()
    dots = th()["dots"]
    dim  = th()["dim_col"]
    console.print(f"[{dim}]{dots}[/{dim}]")
    console.print(f"[{dim}]{dots}[/{dim}]")
    console.print()

    try:
        ascii_logo = pyfiglet.figlet_format(TOOL_NAME, font="slant")
    except Exception:
        ascii_logo = f"  {TOOL_NAME}  "

    _gradient_banner(ascii_logo)

    console.print()
    privilege = f"[bold {th()['danger']}]ROOT/ADMIN[/bold {th()['danger']}]" if is_admin() \
                else f"[{th()['secondary']}]USER[/{th()['secondary']}]"
    theme_badge = f"[{dim}]theme:[/{dim}][{th()['primary']}]{th()['name']}[/{th()['primary']}]"
    console.print(Align.center(
        f"[{dim}]  {VERSION}  ·  [/{dim}]{privilege}"
        f"[{dim}]  ·  {getpass.getuser()}@{platform.node()}"
        f"  ·  {datetime.now().strftime('%H:%M:%S')}  ·  [/{dim}]{theme_badge}"
    ))
    console.print()

# ── CATÉGORIES DU MENU ────────────────────────────────────
def get_cats():
    return [
        (t("c_sys"), th()["cat_sys"], [
            ("01", t("sys1")), ("02", t("sys2")), ("03", t("sys3")),
            ("04", t("sys4")), ("05", t("sys5")), ("06", t("sys6")),
        ]),
        (t("c_net"), th()["cat_net"], [
            ("07", t("net1")), ("08", t("net2")), ("09", t("net3")),
            ("10", t("net4")), ("11", t("net5")), ("12", t("net6")),
        ]),
        (t("c_mon"), th()["cat_mon"], [
            ("13", t("mon1")), ("14", t("mon2")),
        ]),
        (t("c_uti"), th()["cat_uti"], [
            ("15", t("uti1")), ("16", t("uti2")), ("17", t("uti3")),
            ("18", t("uti4")), ("19", t("uti5")),
        ]),
        (t("c_adv"), th()["cat_adv"], [
            ("21", t("adv1")), ("22", t("adv2")), ("23", t("adv3")),
            ("24", t("adv4")), ("25", t("adv5")), ("26", t("adv6")),
            ("27", t("theme")), ("28", t("hist")), ("20", t("lang")), ("00", t("quit")),
        ]),
        # ── NOUVELLE CATÉGORIE v4.1 ──
        (t("c_new"), th()["primary"], [
            ("29", t("new1")), ("30", t("new2")), ("31", t("new3")),
            ("32", t("new4")), ("33", t("new5")), ("34", t("new6")),
            ("35", t("new7")), ("36", t("new8")), ("37", t("new9")),
        ]),
    ]

def _make_panel(title: str, color: str, items: list) -> Panel:
    t_obj = Text()
    for num, label in items:
        t_obj.append(f"[{num}] ", style=f"bold {color}")
        t_obj.append(f"{label}\n", style="white")
    t_obj.rstrip()
    return Panel(
        t_obj, title=f"[{color}]/ {title} \\[/]", border_style=color,
        box=th()["box"], expand=False, width=34
    )

def draw_menu() -> str:
    cats = get_cats()
    pri, sec, dim, mag = th()["primary"], th()["secondary"], th()["dim_col"], th()["cat_uti"]

    console.print(Align.center(_make_panel(*cats[0])))
    conn_line = (f"[{sec}]· · · · · [/{sec}][{pri}]· · · · · · [/{pri}]"
                 f"[{dim}]· · · · · · · · · [/{dim}][{pri}]· · · · · · [/{pri}][{mag}]· · · · · [/{mag}]")
    console.print(Align.center(conn_line))

    grid_mid = Table.grid(padding=(0, 2))
    grid_mid.add_row(*[_make_panel(*c) for c in cats[1:4]])
    console.print(Align.center(grid_mid))

    console.print(Align.center(f"[{dim}]{'· ' * 20}[/{dim}]"))
    console.print(Align.center(_make_panel(*cats[4])))

    # Panneau des nouvelles features
    console.print(Align.center(f"[{pri}]{'★ ' * 20}[/{pri}]"))
    console.print(Align.center(_make_panel(*cats[5])))
    console.print()

    raw = console.input(f"[bold {pri}]{t('prompt')}[/bold {pri}]").strip()
    if raw: CMD_HISTORY.append(raw)
    return raw

def section(label: str, color: str):
    clr()
    banner()
    console.print(Rule(f"[bold {color}]◈  {label.upper()}  ◈[/bold {color}]", style=f"dim {color}"))
    console.print()

def _color_for(choice: str) -> tuple:
    key = choice.zfill(2)
    for cat_title, cat_color, items in get_cats():
        for num, label in items:
            if num == key: return label, cat_color
    return choice, th()["primary"]

# ═══════════════════════════════════════════════════════
#  FEATURES SYSTÈME (inchangées)
# ═══════════════════════════════════════════════════════

def toggle_lang():
    global LANG
    LANG = "en" if LANG == "fr" else "fr"

def system_info():
    u    = platform.uname()
    boot = datetime.fromtimestamp(psutil.boot_time())
    up   = str(datetime.now() - boot).split(".")[0]
    col  = th()["cat_sys"]
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Propriété", style=col, width=20)
    t_ui.add_column("Valeur",    style="white", width=52)
    t_ui.add_row("OS",        f"{u.system} {u.release}")
    t_ui.add_row("Version",   u.version[:54])
    t_ui.add_row("Machine",   u.machine)
    t_ui.add_row("Hostname",  u.node)
    t_ui.add_row("User",      f"[bold]{getpass.getuser()}[/bold]  " +
                              ("[red](ADMIN)[/red]" if is_admin() else "[dim](user)[/dim]"))
    t_ui.add_row("Python",    sys.version.split()[0])
    t_ui.add_row("Uptime",    f"[bold]{up}[/bold]")
    t_ui.add_row("Boot",      boot.strftime("%Y-%m-%d %H:%M"))
    t_ui.add_row("Processor", (u.processor or platform.processor())[:54])
    console.print(t_ui)

def cpu_info():
    freq   = psutil.cpu_freq()
    usage  = psutil.cpu_percent(interval=0.3)
    cores  = psutil.cpu_percent(interval=0.3, percpu=True)
    temps  = {}
    try: temps = psutil.sensors_temperatures()
    except Exception: pass
    col = th()["cat_sys"]
    t_ui = themed_table(border_style=col)
    t_ui.add_column("", style=col, width=20)
    t_ui.add_column("", style="white", width=52)
    t_ui.add_row("Cœurs physiques",  str(psutil.cpu_count(logical=False)))
    t_ui.add_row("Threads logiques", str(psutil.cpu_count(logical=True)))
    t_ui.add_row("Usage global", f"{pct_bar(usage)} [bold]{usage:.1f}%[/bold]")
    if freq:
        t_ui.add_row("Fréquence",  f"{freq.current:.0f} MHz  [dim](max {freq.max:.0f} MHz)[/dim]")
    for name, entries in temps.items():
        for entry in entries[:2]:
            color = "green" if entry.current < 60 else "yellow" if entry.current < 80 else "red"
            t_ui.add_row(f"  Temp {entry.label or name}", f"[{color}]{entry.current:.1f}°C[/{color}]")
    t_ui.add_row("─"*18, "─"*48)
    for i, c in enumerate(cores):
        t_ui.add_row(f"  Core {i}", f"{pct_bar(c, 12)} {c:.1f}%")
    console.print(t_ui)

def ram_info():
    vm   = psutil.virtual_memory()
    swap = psutil.swap_memory()
    gb   = lambda n: f"{n/1e9:.2f} GB"
    col  = th()["cat_sys"]
    t_ui = themed_table(border_style=col)
    t_ui.add_column("", style=col, width=20)
    t_ui.add_column("", style="white", width=52)
    t_ui.add_row("Total RAM",    gb(vm.total))
    t_ui.add_row("Utilisée",     gb(vm.used))
    t_ui.add_row("Disponible",   gb(vm.available))
    t_ui.add_row("Charge RAM",   f"{pct_bar(vm.percent)} [bold]{vm.percent}%[/bold]")
    t_ui.add_row("─"*18, "─"*48)
    t_ui.add_row("Swap Total",   gb(swap.total))
    t_ui.add_row("Swap Utilisé", gb(swap.used))
    t_ui.add_row("Charge Swap",  f"{pct_bar(swap.percent)} {swap.percent}%")
    console.print(t_ui)

def disk_info():
    col  = th()["cat_sys"]
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Lecteur",    style=col, width=14)
    t_ui.add_column("FS",         style="dim", width=8)
    t_ui.add_column("Total",      style="white", width=10)
    t_ui.add_column("Utilisé",    style="white", width=10)
    t_ui.add_column("Libre",      style="white", width=10)
    t_ui.add_column("Charge",     style="white", width=24)
    for p in psutil.disk_partitions():
        try:
            u = psutil.disk_usage(p.mountpoint)
            t_ui.add_row(p.device, p.fstype, f"{u.total/1e9:.1f}G",
                         f"{u.used/1e9:.1f}G", f"{u.free/1e9:.1f}G",
                         f"{pct_bar(u.percent, 12)} {u.percent}%")
        except PermissionError: pass
    try:
        dk = psutil.disk_io_counters()
        if dk:
            console.print()
            info(f"Lecture totale : {dk.read_bytes/1e9:.2f} GB  |  Écriture totale : {dk.write_bytes/1e9:.2f} GB")
    except Exception: pass
    console.print(t_ui)

def uptime_info():
    boot = datetime.fromtimestamp(psutil.boot_time())
    up   = datetime.now() - boot
    h, r = divmod(int(up.total_seconds()), 3600)
    m, s = divmod(r, 60)
    col  = th()["cat_sys"]
    t_ui = themed_table(border_style=col)
    t_ui.add_column("", style=col, width=20)
    t_ui.add_column("", style="white", width=40)
    t_ui.add_row("Boot time", boot.strftime("%Y-%m-%d %H:%M:%S"))
    t_ui.add_row("Uptime",    f"[bold]{h}h {m}m {s}s[/bold]")
    t_ui.add_row("Jours",     str(up.days))
    console.print(t_ui)

def export_sys():
    filename = f"prime_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        vm    = psutil.virtual_memory()
        u_inf = platform.uname()
        boot  = datetime.fromtimestamp(psutil.boot_time())
        up    = str(datetime.now() - boot).split(".")[0]
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"{'='*60}\n  PRIME TOOL {VERSION} — SYSTEM REPORT\n")
            f.write(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*60}\n\n")
            f.write(f"[OS]\n  OS        : {u_inf.system} {u_inf.release}\n")
            f.write(f"  Version   : {u_inf.version}\n  Machine   : {u_inf.machine}\n\n")
            f.write(f"[USER]\n  User      : {getpass.getuser()}@{platform.node()}\n")
            f.write(f"  Admin     : {'OUI' if is_admin() else 'NON'}\n\n")
            f.write(f"[CPU]\n  Processor : {platform.processor()}\n")
            f.write(f"  Cœurs     : {psutil.cpu_count(logical=False)}\n")
            f.write(f"  Threads   : {psutil.cpu_count(logical=True)}\n")
            f.write(f"  Usage     : {psutil.cpu_percent(interval=0.5)}%\n\n")
            f.write(f"[RAM]\n  Total     : {vm.total/1e9:.2f} GB\n")
            f.write(f"  Utilisée  : {vm.used/1e9:.2f} GB ({vm.percent}%)\n\n")
            f.write(f"[UPTIME]\n  Boot      : {boot.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"  Uptime    : {up}\n\n[RÉSEAU]\n")
            for iface, addrs in psutil.net_if_addrs().items():
                for a in addrs:
                    if a.family == socket.AF_INET: f.write(f"  {iface:<16} {a.address}\n")
            f.write(f"\n[DISQUES]\n")
            for p in psutil.disk_partitions():
                try:
                    du = psutil.disk_usage(p.mountpoint)
                    f.write(f"  {p.device:<16} {du.total/1e9:.1f}G  ({du.percent}%)\n")
                except Exception: pass
        success(f"Rapport généré : [bold white]{filename}[/bold white]")
    except Exception as e:
        error(f"Erreur export : {e}")

# ═══════════════════════════════════════════════════════
#  FEATURES RÉSEAU (inchangées)
# ═══════════════════════════════════════════════════════

def network_info():
    hostname = socket.gethostname()
    try: lip = socket.gethostbyname(hostname)
    except socket.error: lip = "N/A"

    pub_ip, geo_loc, org = "N/A", "N/A", "N/A"
    try:
        req = urllib.request.Request("https://ipinfo.io/json", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode())
            pub_ip  = data.get("ip", "?")
            geo_loc = f"{data.get('city','?')}, {data.get('region','?')}, {data.get('country','?')}"
            org     = data.get("org", "?")
    except Exception: pass

    net = psutil.net_io_counters()
    col = th()["cat_net"]
    t_ui = themed_table(border_style=col)
    t_ui.add_column("", style=col, width=22)
    t_ui.add_column("", style="white", width=48)
    t_ui.add_row("Hostname",     hostname)
    t_ui.add_row("IP Locale",    lip)
    t_ui.add_row("IP Publique",  f"[bold {th()['primary']}]{pub_ip}[/bold {th()['primary']}]")
    t_ui.add_row("Localisation", geo_loc)
    t_ui.add_row("Fournisseur",  org)
    t_ui.add_row("─"*20, "─"*46)
    for iface, addrs in psutil.net_if_addrs().items():
        for a in addrs:
            if a.family == socket.AF_INET and a.address not in ("127.0.0.1","0.0.0.0"):
                mask = f"  [dim]/ {a.netmask}[/dim]" if a.netmask else ""
                t_ui.add_row(f"  {iface}", f"{a.address}{mask}")
    t_ui.add_row("─"*20, "─"*46)
    t_ui.add_row("Envoyé",      f"{net.bytes_sent/1e6:.2f} MB")
    t_ui.add_row("Reçu",        f"{net.bytes_recv/1e6:.2f} MB")
    t_ui.add_row("Paquets ↑",   str(net.packets_sent))
    t_ui.add_row("Paquets ↓",   str(net.packets_recv))
    console.print(t_ui)

def ping_test():
    col  = th()["cat_net"]
    host = console.input(f"[{col}]  Host [dim](default: 8.8.8.8)[/dim] ❯ [/{col}]").strip() or "8.8.8.8"
    host = host.split()[0]
    count = console.input(f"[{col}]  Pings [dim](default: 4)[/dim] ❯ [/{col}]").strip() or "4"
    if not count.isdigit(): count = "4"
    console.print(f"\n[dim {col}]Ping → {host}  (x{count})...[/dim {col}]\n")
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    subprocess.run(["ping", param, count, host])

def net_stats():
    col  = th()["cat_net"]
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Interface",  style=col, width=18)
    t_ui.add_column("Envoyé",     style="white", width=14)
    t_ui.add_column("Reçu",       style="white", width=14)
    t_ui.add_column("Paquets ↑",  style="white", width=12)
    t_ui.add_column("Paquets ↓",  style="white", width=12)
    t_ui.add_column("Err",        style="red", width=8)
    for name, s in psutil.net_io_counters(pernic=True).items():
        err_total = s.errin + s.errout
        t_ui.add_row(name, f"{s.bytes_sent/1e6:.1f} MB", f"{s.bytes_recv/1e6:.1f} MB",
                     str(s.packets_sent), str(s.packets_recv),
                     f"[red]{err_total}[/red]" if err_total > 0 else "[dim]0[/dim]")
    console.print(t_ui)

def dns_lookup():
    col  = th()["cat_net"]
    host = console.input(f"[{col}]  Domaine ❯ [/{col}]").strip()
    if not host: return
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Type",      style=col, width=12)
    t_ui.add_column("Résultat",  style="white", width=54)
    try: t_ui.add_row("IPv4", socket.gethostbyname(host))
    except Exception as e: t_ui.add_row("Erreur IPv4", str(e))
    try:
        for item in socket.getaddrinfo(host, None):
            if item[0].name == "AF_INET6":
                t_ui.add_row("IPv6", item[4][0])
                break
    except Exception: pass
    try: t_ui.add_row("FQDN", socket.getfqdn(host))
    except Exception: pass
    console.print(t_ui)

def port_checker():
    col   = th()["cat_net"]
    host  = console.input(f"[{col}]  Host [dim](default: localhost)[/dim] ❯ [/{col}]").strip() or "localhost"
    raw   = console.input(f"[{col}]  Ports [dim](ex: 80,443,8080 ou vide=communs)[/dim] ❯ [/{col}]").strip()
    known = { 21:"FTP", 22:"SSH", 23:"Telnet", 25:"SMTP", 53:"DNS", 80:"HTTP",
              110:"POP3", 143:"IMAP", 443:"HTTPS", 3306:"MySQL", 3389:"RDP",
              5432:"PgSQL", 8080:"HTTP-Alt", 27017:"MongoDB" }
    ports = ([int(p) for p in raw.split(",") if p.strip().isdigit()] if raw else list(known.keys()))
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Port", style=col, width=8)
    t_ui.add_column("État", style="white", width=14)
    t_ui.add_column("Service", style="dim", width=16)
    t_ui.add_column("Latence", style="dim", width=12)

    def check_port(port):
        try:
            s = socket.socket(); s.settimeout(0.8)
            start = time.time()
            open_ = s.connect_ex((host, port)) == 0
            lat   = (time.time() - start) * 1000
            s.close()
            return port, open_, lat
        except Exception: return port, False, 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        results = list(ex.map(check_port, ports))

    for port, open_, lat in sorted(results, key=lambda x: x[0]):
        status  = f"[{th()['success']}]OPEN[/{th()['success']}]" if open_ else f"[{th()['danger']}]CLOSED[/{th()['danger']}]"
        lat_str = f"[dim]{lat:.0f}ms[/dim]" if open_ else "[dim]—[/dim]"
        t_ui.add_row(str(port), status, known.get(port,"—"), lat_str)
    console.print(t_ui)

def scan_lan():
    col = th()["cat_net"]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try: s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]
    except Exception: ip = "192.168.1.1"
    finally: s.close()

    base_ip = ".".join(ip.split(".")[:-1]) + "."
    console.print(f"[dim {col}]Scan asynchrone de {base_ip}0/24 ... (patientez)[/dim {col}]\n")

    def ping_ip(target):
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "1", "-w", "500", target]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True)
                if "TTL=" in res.stdout: return target
            except Exception: pass
        else:
            cmd = ["ping", "-c", "1", "-W", "1", target]
            res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0: return target
        return None

    active_ips = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        ips = [base_ip + str(i) for i in range(1, 255)]
        for res in executor.map(ping_ip, ips):
            if res:
                active_ips.append(res)
                try: hname = socket.gethostbyaddr(res)[0]
                except Exception: hname = "?"
                console.print(f"  [{th()['success']}][+][/{th()['success']}] {res:<18} [dim]{hname}[/dim]")

    console.print(f"\n[{th()['primary']}]Terminé. {len(active_ips)} hôte(s) trouvé(s).[/{th()['primary']}]")

# ═══════════════════════════════════════════════════════
#  FEATURES MONITORING (inchangées)
# ═══════════════════════════════════════════════════════

def live_monitor():
    col = th()["cat_mon"]
    console.print(f"[dim {col}]  Ctrl+C pour arrêter[/dim {col}]\n")
    net_prev = psutil.net_io_counters()
    prev_time = time.time()
    try:
        while True:
            clr()
            banner()
            now, delta = time.time(), (time.time() - prev_time or 1)
            cpu = psutil.cpu_percent(interval=0.4)
            ram = psutil.virtual_memory().percent
            net_cur = psutil.net_io_counters()
            dk = psutil.disk_io_counters()
            ul_rate = (net_cur.bytes_sent - net_prev.bytes_sent) / delta / 1024
            dl_rate = (net_cur.bytes_recv - net_prev.bytes_recv) / delta / 1024
            net_prev, prev_time = net_cur, now

            t_ui = themed_table(title=f"[dim]🟢 Live — {datetime.now().strftime('%H:%M:%S')}[/dim]", border_style=col)
            t_ui.add_column("Métrique",  style=col, width=14)
            t_ui.add_column("Barre",     style="white", width=20)
            t_ui.add_column("Valeur",    style="white", width=16)

            col_c = "green" if cpu < 60 else "yellow" if cpu < 85 else "red"
            col_r = "green" if ram < 60 else "yellow" if ram < 85 else "red"
            t_ui.add_row("CPU",     pct_bar(cpu),  f"[bold {col_c}]{cpu:.1f}%[/bold {col_c}]")
            t_ui.add_row("RAM",     pct_bar(ram),  f"[bold {col_r}]{ram:.1f}%[/bold {col_r}]")
            t_ui.add_row("Upload",  f"[blue]{'▸'*16}[/blue]",  f"[blue]{ul_rate:.1f} KB/s[/blue]")
            t_ui.add_row("Downld",  f"[green]{'▸'*16}[/green]",f"[green]{dl_rate:.1f} KB/s[/green]")
            if dk:
                t_ui.add_row("Disk R", f"[magenta]{'▸'*16}[/magenta]", f"[magenta]{dk.read_bytes/1e6:.0f}MB[/magenta]")
                t_ui.add_row("Disk W", f"[yellow]{'▸'*16}[/yellow]", f"[yellow]{dk.write_bytes/1e6:.0f}MB[/yellow]")

            top_cpu = sorted(psutil.process_iter(["name","cpu_percent"]),
                             key=lambda p: p.info.get("cpu_percent") or 0, reverse=True)[:3]
            for p in top_cpu:
                name, pct = (p.info.get("name") or "?")[:14], p.info.get("cpu_percent") or 0
                if pct > 0.5: t_ui.add_row(f"[dim]{name}[/dim]", f"[dim]{pct_bar(min(pct,100), 12)}[/dim]", f"[dim]{pct:.1f}%[/dim]")
            console.print(Align.center(t_ui))
            time.sleep(1)
    except KeyboardInterrupt: pass

def top_processes():
    col   = th()["cat_mon"]
    procs = []
    for p in psutil.process_iter(["pid","name","cpu_percent","memory_info","status","username"]):
        try: procs.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): pass

    procs = sorted(procs, key=lambda x: x.get("cpu_percent") or 0, reverse=True)[:20]
    t_ui = themed_table(border_style=col)
    t_ui.add_column("PID",   style="dim", width=8)
    t_ui.add_column("Nom",   style="white", width=24)
    t_ui.add_column("User",  style="dim", width=14)
    t_ui.add_column("Status",style="dim", width=12)
    t_ui.add_column("CPU",   style=col, width=8)
    t_ui.add_column("RAM",   style="green", width=10)
    t_ui.add_column("Barre", style=col, width=18)

    for p in procs:
        cpu = p.get("cpu_percent") or 0
        ram = (p.get("memory_info").rss / 1e6) if p.get("memory_info") else 0
        name = (p.get("name") or "?")[:24]
        user = (p.get("username") or "?")[:14]
        t_ui.add_row(str(p["pid"]), name, user, p.get("status","?"),
                     f"{cpu:.1f}%", f"{ram:.0f} MB", pct_bar(min(cpu,100)))
    console.print(t_ui)

# ═══════════════════════════════════════════════════════
#  FEATURES UTILITAIRES (inchangées)
# ═══════════════════════════════════════════════════════

def hash_gen():
    col  = th()["cat_uti"]
    text = console.input(f"[{col}]  Texte ❯ [/{col}]")
    enc  = text.encode()
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Algo", style=col, width=10)
    t_ui.add_column("Résultat", style="white", width=70)
    t_ui.add_row("MD5",     hashlib.md5(enc).hexdigest())
    t_ui.add_row("SHA1",    hashlib.sha1(enc).hexdigest())
    t_ui.add_row("SHA256",  hashlib.sha256(enc).hexdigest())
    t_ui.add_row("SHA512",  hashlib.sha512(enc).hexdigest())
    t_ui.add_row("SHA3-256",hashlib.sha3_256(enc).hexdigest())
    console.print(t_ui)

def password_gen():
    col = th()["cat_uti"]
    try: n = int(console.input(f"[{col}]  Longueur [dim](default 18)[/dim] ❯ [/{col}]") or "18")
    except ValueError: n = 18

    sets = {
        "alpha": string.ascii_letters,
        "digits": string.digits,
        "spec": "!@#$%^&*()-_=+[]{}|;:,.<>?"
    }
    chars = sets["alpha"] + sets["digits"] + sets["spec"]

    t_ui = themed_table(border_style=col)
    t_ui.add_column("#", style=f"dim {col}", width=4)
    t_ui.add_column("Mot de passe", style="bold white", width=50)
    t_ui.add_column("Force", style="white", width=20)

    def strength(pwd):
        sc = 0
        if len(pwd) >= 12: sc += 30
        if any(c.isupper() for c in pwd): sc += 20
        if any(c.isdigit() for c in pwd): sc += 20
        if any(c in sets["spec"] for c in pwd): sc += 30
        return sc

    for i in range(5):
        pwd = (random.choice(sets["alpha"].upper()) +
               random.choice(sets["digits"]) +
               random.choice(sets["spec"]) +
               ''.join(random.choice(chars) for _ in range(n - 3)))
        pwd_list = list(pwd); random.shuffle(pwd_list); pwd = ''.join(pwd_list)
        sc = strength(pwd)
        t_ui.add_row(str(i+1), pwd, f"{pct_bar(sc, 10)} {sc}/100")
    console.print(t_ui)

def pass_checker():
    col = th()["cat_uti"]
    pwd = console.input(f"[{col}]  Mot de passe à tester ❯ [/{col}]")
    score = 0
    criteria = [
        ("Longueur ≥ 8",  len(pwd) >= 8,  20),
        ("Longueur ≥ 12", len(pwd) >= 12, 20),
        ("Majuscules",    any(c.isupper() for c in pwd), 15),
        ("Minuscules",    any(c.islower() for c in pwd), 15),
        ("Chiffres",      any(c.isdigit() for c in pwd), 15),
        ("Spéciaux",      any(c in string.punctuation for c in pwd), 15),
    ]
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Critère", style="white", width=30)
    t_ui.add_column("Statut",  width=15)
    t_ui.add_column("Points",  style="dim", width=10)
    for label, ok, pts in criteria:
        if ok: score += pts
        t_ui.add_row(label, "[green]✔[/green]" if ok else "[red]✘[/red]",
                     f"+{pts}" if ok else "[dim]0[/dim]")
    t_ui.add_row("─"*28, "─"*13, "─"*8)
    lvl = "FAIBLE" if score < 40 else "MOYEN" if score < 70 else "FORT" if score < 90 else "EXCELLENT"
    lvl_col = "red" if score < 40 else "yellow" if score < 70 else "green" if score < 90 else "bright_green"
    t_ui.add_row("Score Global", f"[{lvl_col}]{lvl}[/{lvl_col}]", f"[bold]{score}/100[/bold]")
    t_ui.add_row("", f"{pct_bar(score, 14)}", "")
    console.print(t_ui)

def base64_tool():
    col  = th()["cat_uti"]
    mode = console.input(f"[{col}]  (e)ncode / (d)ecode ❯ [/{col}]").strip().lower()
    text = console.input(f"[{col}]  Texte ❯ [/{col}]")
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Action",   style=col, width=10)
    t_ui.add_column("Résultat", style="white", width=64)
    try:
        if mode in ("e","encode"):
            t_ui.add_row("Encodé", base64.b64encode(text.encode()).decode())
        else:
            t_ui.add_row("Décodé", base64.b64decode(text.encode()).decode())
    except Exception as e:
        t_ui.add_row("[red]Erreur[/red]", str(e))
    console.print(t_ui)

def clean_temp():
    col = th()["cat_uti"]
    console.print(f"[dim {col}]  Nettoyage des fichiers temporaires en cours...[/dim {col}]")
    count = 0
    temp_dirs = []
    if os.name == "nt":
        temp_dirs = [os.environ.get("TEMP"), os.environ.get("TMP"), "C:\\Windows\\Temp"]
    else:
        temp_dirs = ["/tmp", "/var/tmp"]
    for temp_dir in temp_dirs:
        if not temp_dir or not os.path.exists(temp_dir): continue
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for name in files:
                try: os.remove(os.path.join(root, name)); count += 1
                except Exception: pass
            for name in dirs:
                try: os.rmdir(os.path.join(root, name))
                except Exception: pass
    success(f"Fichiers temporaires nettoyés ({count} éléments supprimés) !")

# ═══════════════════════════════════════════════════════
#  FEATURES AVANCÉES (inchangées)
# ═══════════════════════════════════════════════════════

def traceroute():
    col  = th()["cat_adv"]
    host = console.input(f"[{col}]  Cible [dim](default: 8.8.8.8)[/dim] ❯ [/{col}]").strip() or "8.8.8.8"
    console.print(f"\n[dim {col}]Traceroute → {host}...[/dim {col}]\n")
    cmd = (["tracert", host] if platform.system().lower() == "windows"
           else ["traceroute", "-m", "20", host])
    try: subprocess.run(cmd)
    except FileNotFoundError: error("traceroute/tracert non disponible sur ce système.")

def whois_geoip():
    col  = th()["cat_adv"]
    host = console.input(f"[{col}]  IP ou Domaine ❯ [/{col}]").strip()
    if not host: return
    try: ip = socket.gethostbyname(host)
    except Exception: ip = host

    t_ui = themed_table(border_style=col)
    t_ui.add_column("Champ",  style=col, width=22)
    t_ui.add_column("Valeur", style="white", width=54)
    t_ui.add_row("Cible", host)
    t_ui.add_row("IP", ip)

    try:
        safe_ip = urllib.parse.quote(ip)
        req = urllib.request.Request(f"https://ipinfo.io/{safe_ip}/json",
                                     headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        fields = [
            ("Hostname","hostname"), ("Ville","city"), ("Région","region"),
            ("Pays","country"), ("Postal","postal"), ("Org","org"),
            ("Fuseau","timezone"), ("Coords","loc"),
        ]
        for label, key in fields:
            val = data.get(key, "—")
            if val and val != "—": t_ui.add_row(label, str(val))
    except Exception as e: t_ui.add_row("Erreur GeoIP", str(e))
    console.print(t_ui)

def qr_ascii():
    col  = th()["cat_adv"]
    text = console.input(f"[{col}]  Texte/URL pour QR ❯ [/{col}]").strip()
    if not text: return
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
    rng, size = random.Random(seed), 21
    console.print(f"\n  [dim]QR ASCII pour : [bold]{text[:40]}[/bold][/dim]\n")
    pri = th()["primary"]
    finder = set()
    for r in range(7):
        for c in range(7):
            finder.update([(r, c), (r, size-7+c), (size-7+r, c)])
    line_top = f"  [bold {pri}]{'██' * (size + 2)}[/bold {pri}]"
    console.print(line_top)
    for row in range(size):
        line = f"  [bold {pri}]██[/bold {pri}]"
        for col_i in range(size):
            line += f"[bold {pri}]██[/bold {pri}]" if (row,col_i) in finder or rng.randint(0,1) else "  "
        line += f"[bold {pri}]██[/bold {pri}]"
        console.print(line)
    console.print(line_top)
    console.print()
    info("Pour un vrai QR Code : pip install qrcode puis qr.make(text)")

def converter():
    col = th()["cat_adv"]
    console.print(f"  [{col}]Catégories :[/{col}]  [dim]1[/dim] Octets  [dim]2[/dim] Temps  [dim]3[/dim] Température  [dim]4[/dim] Débit réseau")
    cat = console.input(f"[{col}]  Catégorie ❯ [/{col}]").strip()
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Unité",  style=col, width=22)
    t_ui.add_column("Valeur", style="bold white", width=30)
    raw = console.input(f"[{col}]  Valeur ❯ [/{col}]").strip()
    try: n = float(raw)
    except ValueError: error("Valeur invalide."); return
    if cat == "1":
        t_ui.add_row("Bytes",     f"{n:,.0f}")
        t_ui.add_row("Megabytes", f"{n/1e6:,.3f}")
        t_ui.add_row("Gigabytes", f"{n/1e9:,.3f}")
        t_ui.add_row("Gibibytes", f"{n/1073741824:,.6f}")
    elif cat == "2":
        h, rem = divmod(n, 3600); m, s = divmod(rem, 60)
        t_ui.add_row("Heures",  f"{n/3600:,.6f}")
        t_ui.add_row("Formaté", f"{int(h)}h {int(m)}m {s:.2f}s")
    elif cat == "3":
        t_ui.add_row("Celsius",    f"{n:.2f} °C")
        t_ui.add_row("Fahrenheit", f"{n*9/5+32:.2f} °F")
    elif cat == "4":
        t_ui.add_row("Mbps", f"{n:,.2f}")
        t_ui.add_row("MB/s", f"{n/8:,.3f}")
    else: error("Catégorie invalide."); return
    console.print(t_ui)

def suspicious_processes():
    col = th()["cat_adv"]
    SUSPECT_NAMES = {
        "nc","ncat","netcat","nmap","masscan","wireshark","tcpdump","mimikatz",
        "msfconsole","msfvenom","hydra","john","hashcat","aircrack","aireplay",
        "airmon","ettercap","bettercap","responder","sqlmap","burpsuite",
        "metasploit","cobaltstrike","empire","rat","keylogger","stealer",
        "cryptominer","xmrig","minergate"
    }
    SUSPECT_PORTS = {4444, 1337, 31337, 6666, 8888, 9999, 12345, 54321, 65535}
    t_ui = themed_table(border_style=col)
    t_ui.add_column("PID",    style="dim", width=8)
    t_ui.add_column("Nom",    style="bold white", width=22)
    t_ui.add_column("Raison", style="yellow", width=26)
    t_ui.add_column("User",   style="dim", width=14)
    t_ui.add_column("CMD",    style="dim", width=26)
    found = 0
    for p in psutil.process_iter(["pid","name","username","cmdline","connections"]):
        try:
            info_p = p.info; name_l = (info_p.get("name") or "").lower(); reasons = []
            for s in SUSPECT_NAMES:
                if s in name_l: reasons.append(f"[yellow]nom '{s}'[/yellow]"); break
            try:
                for conn in (info_p.get("connections") or []):
                    if hasattr(conn,"laddr") and conn.laddr and conn.laddr.port in SUSPECT_PORTS:
                        reasons.append(f"[red]port {conn.laddr.port}[/red]")
                    if hasattr(conn,"raddr") and conn.raddr and conn.raddr.port in SUSPECT_PORTS:
                        reasons.append(f"[red]→ port {conn.raddr.port}[/red]")
            except (psutil.AccessDenied, psutil.NoSuchProcess): pass
            if reasons:
                found += 1
                t_ui.add_row(str(info_p["pid"]), (info_p.get("name") or "?")[:22],
                             ", ".join(reasons[:2]), (info_p.get("username") or "?")[:14],
                             " ".join((info_p.get("cmdline") or []))[:26])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): pass
    if found == 0: t_ui.add_row("—", "[green]Aucun suspect détecté[/green]", "—","—","—")
    console.print(t_ui)
    if found > 0: warn(f"{found} processus suspect(s) trouvé(s) — vérifiez manuellement.")

def speedtest_basic():
    col = th()["cat_adv"]
    console.print(f"\n[dim {col}]Test de débit en cours (téléchargement)...[/dim {col}]\n")
    TEST_URL = "http://speedtest.tele2.net/1MB.zip"
    FALLBACK = "https://httpbin.org/bytes/524288"
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Métrique", style=col, width=22)
    t_ui.add_column("Valeur",   style="bold white", width=30)
    try:
        start = time.time(); urllib.request.urlopen("https://www.google.com", timeout=3)
        t_ui.add_row("Latence HTTP (Google)", f"{(time.time()-start)*1000:.0f} ms")
    except Exception: t_ui.add_row("Latence HTTP", "[red]N/A[/red]")
    for url, label in [(TEST_URL,"1MB.zip"),(FALLBACK,"512KB httpbin")]:
        try:
            start = time.time()
            with urllib.request.urlopen(url, timeout=10) as resp: data = resp.read()
            duration = time.time() - start; size_mb = len(data) / 1e6
            t_ui.add_row(f"Download ({label})",
                         f"[bold green]{size_mb/duration*8:.2f} Mbps[/bold green]  [dim]({size_mb:.2f}MB en {duration:.1f}s)[/dim]")
            break
        except Exception as e: t_ui.add_row(f"Download ({label})", f"[red]Erreur : {e}[/red]")
    t_ui.add_row("─"*20, "─"*28)
    t_ui.add_row("[dim]Note[/dim]", "[dim]Test minimal — pour un vrai speedtest : speedtest-cli[/dim]")
    console.print(t_ui)

def show_history():
    col = th()["cat_adv"]
    if not CMD_HISTORY: info("Aucune commande dans l'historique."); return
    t_ui = themed_table(border_style=col)
    t_ui.add_column("#",       style=f"dim {col}", width=6)
    t_ui.add_column("Commande",style="white", width=20)
    t_ui.add_column("Label",   style="dim", width=30)
    for i, cmd in enumerate(CMD_HISTORY, 1):
        label, _ = _color_for(cmd)
        t_ui.add_row(str(i), cmd, label)
    console.print(t_ui)

def change_theme():
    global CURRENT_THEME_IDX
    old_name = th()["name"]
    CURRENT_THEME_IDX = (CURRENT_THEME_IDX + 1) % len(THEME_NAMES)
    success(f"Thème : [bold]{old_name}[/bold] → [bold]{th()['name']}[/bold]")
    time.sleep(0.8)

# ═══════════════════════════════════════════════════════
#  ★ NOUVELLES FEATURES v4.1.0
# ═══════════════════════════════════════════════════════

# ── 29 · FIREWALL RULES ─────────────────────────────────
def firewall_rules():
    """Affiche les règles firewall actives (iptables ou netsh selon l'OS)."""
    col = th()["primary"]
    system = platform.system().lower()

    if system == "windows":
        console.print(f"[dim {col}]  Récupération des règles Windows Firewall...[/dim {col}]\n")
        try:
            result = subprocess.run(
                ["netsh", "advfirewall", "firewall", "show", "rule", "name=all"],
                capture_output=True, text=True, timeout=10
            )
            lines = result.stdout.splitlines()
            t_ui = themed_table(border_style=col)
            t_ui.add_column("Nom",       style="bold white", width=30)
            t_ui.add_column("Enabled",   style="white", width=10)
            t_ui.add_column("Direction", style=col, width=12)
            t_ui.add_column("Action",    style="white", width=10)
            t_ui.add_column("Protocole", style="dim", width=12)

            rule = {}
            for line in lines:
                line = line.strip()
                if line.startswith("Rule Name:"):   rule["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("Enabled:"):   rule["enabled"] = line.split(":", 1)[1].strip()
                elif line.startswith("Direction:"): rule["direction"] = line.split(":", 1)[1].strip()
                elif line.startswith("Action:"):    rule["action"] = line.split(":", 1)[1].strip()
                elif line.startswith("Protocol:"):
                    rule["protocol"] = line.split(":", 1)[1].strip()
                    if rule.get("enabled","No") == "Yes":
                        action_col = "green" if rule.get("action","").lower() == "allow" else "red"
                        t_ui.add_row(
                            rule.get("name","?")[:30],
                            f"[{action_col}]{rule.get('enabled','?')}[/{action_col}]",
                            rule.get("direction","?"),
                            f"[{action_col}]{rule.get('action','?')}[/{action_col}]",
                            rule.get("protocol","?")
                        )
                    rule = {}
            console.print(t_ui)
        except FileNotFoundError:
            error("netsh non disponible.")
        except subprocess.TimeoutExpired:
            error("Timeout lors de la récupération des règles.")

    else:
        # Linux — essai iptables puis nftables
        console.print(f"[dim {col}]  Récupération des règles iptables...[/dim {col}]\n")
        tried_nft = False

        def try_iptables():
            for cmd in (["iptables", "-L", "-n", "-v", "--line-numbers"],
                        ["sudo", "iptables", "-L", "-n", "-v", "--line-numbers"]):
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
                    if res.returncode == 0 and res.stdout.strip():
                        return res.stdout
                except (FileNotFoundError, subprocess.TimeoutExpired): pass
            return None

        output = try_iptables()

        if output:
            t_ui = themed_table(border_style=col)
            t_ui.add_column("#",      style=f"dim {col}", width=6)
            t_ui.add_column("Chain",  style=col, width=12)
            t_ui.add_column("Règle",  style="white", width=56)

            chain = "?"
            count = 0
            for line in output.splitlines():
                if line.startswith("Chain"):
                    chain = line.split()[1]
                elif line.strip() and not line.startswith("pkts") and not line.startswith("num"):
                    parts = line.split()
                    if len(parts) >= 4:
                        count += 1
                        target = parts[2] if len(parts) > 2 else "?"
                        tcol = "green" if "ACCEPT" in target else "red" if "DROP" in target or "REJECT" in target else "yellow"
                        t_ui.add_row(str(count), chain, f"[{tcol}]{line.strip()[:56]}[/{tcol}]")
            if count == 0:
                t_ui.add_row("—", "—", "[dim]Aucune règle trouvée (tables vides)[/dim]")
            console.print(t_ui)
        else:
            tried_nft = True
            info("iptables indisponible ou accès refusé, tentative avec nftables...")
            try:
                res = subprocess.run(["nft", "list", "ruleset"], capture_output=True, text=True, timeout=8)
                if res.returncode == 0 and res.stdout.strip():
                    console.print(f"[{col}]{res.stdout}[/{col}]")
                else:
                    warn("Aucune règle firewall trouvée. Lancez en root pour un accès complet.")
            except FileNotFoundError:
                error("Ni iptables ni nftables disponibles sur ce système.")

        # Essai ufw status si dispo
        try:
            res_ufw = subprocess.run(["ufw", "status", "verbose"], capture_output=True, text=True, timeout=5)
            if res_ufw.returncode == 0 and res_ufw.stdout.strip():
                console.print()
                console.print(Rule(f"[{col}]UFW Status[/{col}]", style=f"dim {col}"))
                console.print(f"[{col}]{res_ufw.stdout}[/{col}]")
        except (FileNotFoundError, subprocess.TimeoutExpired): pass

    info("Utilisez les droits root/admin pour voir toutes les règles.")


# ── 30 · SSH AUDIT ──────────────────────────────────────
def ssh_audit():
    """Audite la configuration SSH du serveur local."""
    col = th()["primary"]

    SSH_CONF_PATHS = [
        "/etc/ssh/sshd_config",
        "/etc/sshd_config",
        "C:\\ProgramData\\ssh\\sshd_config",
    ]

    conf_path = None
    for p in SSH_CONF_PATHS:
        if os.path.isfile(p):
            conf_path = p
            break

    t_ui = themed_table(border_style=col)
    t_ui.add_column("Paramètre",   style=col, width=26)
    t_ui.add_column("Valeur",      style="bold white", width=24)
    t_ui.add_column("Statut",      width=20)
    t_ui.add_column("Recommandé",  style="dim", width=20)

    CHECKS = {
        "Port":                    ("22",      "≠ 22 = mieux",    False),
        "PermitRootLogin":         ("no",      "no",              True),
        "PasswordAuthentication":  ("no",      "no",              True),
        "PubkeyAuthentication":    ("yes",     "yes",             True),
        "PermitEmptyPasswords":    ("no",      "no",              True),
        "X11Forwarding":           ("no",      "no",              True),
        "MaxAuthTries":            ("3",       "≤ 3",             False),
        "LoginGraceTime":          ("30",      "≤ 30s",           False),
        "AllowAgentForwarding":    ("no",      "no",              True),
        "ClientAliveInterval":     ("300",     "≤ 300",           False),
        "Protocol":                ("2",       "2 uniquement",    True),
        "UsePAM":                  ("yes",     "yes",             True),
        "StrictModes":             ("yes",     "yes",             True),
    }

    config = {}
    if conf_path:
        try:
            with open(conf_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split(None, 1)
                        if len(parts) == 2:
                            config[parts[0]] = parts[1].strip()
        except PermissionError:
            warn(f"Accès refusé à {conf_path} — lancez en root.")

        t_ui.add_row(f"[dim]Fichier[/dim]", conf_path, "[dim]—[/dim]", "")
        t_ui.add_row("─"*24, "─"*22, "─"*18, "─"*18)

        score, total = 0, 0
        for param, (recommended, hint, exact) in CHECKS.items():
            val = config.get(param, "[dim]non défini[/dim]")
            raw = config.get(param, "")
            total += 1
            if exact:
                ok = (raw.lower() == recommended.lower())
            else:
                # Port : ≠ 22 ; MaxAuthTries : ≤ 3 ; etc.
                try:
                    n = int(raw)
                    if "≠" in hint: ok = (n != int(recommended))
                    elif "≤" in hint: ok = (n <= int(recommended.split("≤")[-1].strip().split()[0]))
                    else: ok = (raw.lower() == recommended.lower())
                except (ValueError, AttributeError): ok = False
            if ok: score += 1
            status = f"[green]✔ OK[/green]" if ok else f"[red]✘ KO[/red]"
            t_ui.add_row(param, val if val else "[dim]—[/dim]", status, hint)

        t_ui.add_row("─"*24, "─"*22, "─"*18, "─"*18)
        pct = int(score / total * 100) if total else 0
        pct_c = "green" if pct >= 75 else "yellow" if pct >= 50 else "red"
        t_ui.add_row("Score SSH", f"[bold {pct_c}]{score}/{total}  ({pct}%)[/bold {pct_c}]",
                     f"{pct_bar(pct, 12)}", "")
    else:
        t_ui.add_row("sshd_config", "[red]Introuvable[/red]", "—", "—")
        info("SSH n'est peut-être pas installé ou vous n'êtes pas sur Linux/Windows Server.")

    console.print(t_ui)

    # Vérifier si le service SSH tourne
    ssh_running = False
    for p in psutil.process_iter(["name"]):
        try:
            n = (p.info.get("name") or "").lower()
            if "sshd" in n or "ssh" in n:
                ssh_running = True; break
        except (psutil.NoSuchProcess, psutil.AccessDenied): pass
    console.print()
    if ssh_running:
        success("Service sshd détecté comme actif.")
    else:
        info("Aucun processus sshd détecté (service arrêté ou non installé).")


# ── 31 · WATCHER LOGS ───────────────────────────────────
def watcher_logs():
    """Suit un fichier log en temps réel avec colorisation par niveau."""
    col = th()["primary"]

    DEFAULT_LOGS = {
        "1": "/var/log/syslog",
        "2": "/var/log/auth.log",
        "3": "/var/log/kern.log",
        "4": "/var/log/nginx/access.log",
        "5": "/var/log/apache2/access.log",
    }

    if platform.system().lower() == "windows":
        DEFAULT_LOGS = {
            "1": "C:\\Windows\\Logs\\WindowsUpdate\\WindowsUpdate.log",
        }

    console.print(f"[{col}]  Logs disponibles :[/{col}]")
    for k, v in DEFAULT_LOGS.items():
        exists = "[green]✔[/green]" if os.path.isfile(v) else "[red]✘[/red]"
        console.print(f"  [dim]{k}[/dim]  {exists}  {v}")
    console.print()

    choice = console.input(f"[{col}]  Numéro ou chemin personnalisé ❯ [/{col}]").strip()
    log_path = DEFAULT_LOGS.get(choice, choice)

    if not os.path.isfile(log_path):
        error(f"Fichier introuvable : {log_path}")
        return

    try:
        n_lines = int(console.input(f"[{col}]  Dernières lignes à afficher [dim](default: 20)[/dim] ❯ [/{col}]").strip() or "20")
    except ValueError:
        n_lines = 20

    def colorize(line: str) -> str:
        l = line.lower()
        if any(k in l for k in ("error","err","fatal","critical","crit","alert","emerg")):
            return f"[red]{line}[/red]"
        elif any(k in l for k in ("warn","warning")):
            return f"[yellow]{line}[/yellow]"
        elif any(k in l for k in ("info","notice","debug")):
            return f"[dim]{line}[/dim]"
        elif any(k in l for k in ("success","ok","started","ready","listening")):
            return f"[green]{line}[/green]"
        elif any(k in l for k in ("fail","denied","refused","invalid","unauthorized")):
            return f"[bold red]{line}[/bold red]"
        return line

    console.print(f"\n[dim {col}]  Watching : {log_path}  —  Ctrl+C pour arrêter[/dim {col}]\n")

    # Afficher les dernières lignes
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            all_lines = f.readlines()
            for line in all_lines[-n_lines:]:
                console.print(f"  {colorize(line.rstrip())}")
    except PermissionError:
        error(f"Accès refusé à {log_path} — essayez en root.")
        return

    # Suivi en temps réel
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, 2)  # fin du fichier
            while True:
                line = f.readline()
                if line:
                    ts = datetime.now().strftime("%H:%M:%S")
                    console.print(f"  [{th()['dim_col']}]{ts}[/{th()['dim_col']}]  {colorize(line.rstrip())}")
                else:
                    time.sleep(0.3)
    except KeyboardInterrupt:
        console.print(f"\n[{col}]  Watcher arrêté.[/{col}]")
    except PermissionError:
        error(f"Accès refusé.")


# ── 32 · SERVICES MANAGER ───────────────────────────────
def services_manager():
    """Liste les services système avec leur statut."""
    col = th()["primary"]
    system = platform.system().lower()

    t_ui = themed_table(border_style=col)
    t_ui.add_column("Service",  style="bold white", width=30)
    t_ui.add_column("Statut",   width=14)
    t_ui.add_column("Type",     style="dim", width=10)
    t_ui.add_column("PID",      style="dim", width=8)
    t_ui.add_column("Description", style="dim", width=28)

    if system == "windows":
        try:
            result = subprocess.run(
                ["sc", "query", "type=", "all", "state=", "all"],
                capture_output=True, text=True, timeout=10
            )
            svc = {}
            count = 0
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith("SERVICE_NAME:"):
                    svc["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("STATE"):
                    raw_state = line.split(":", 1)[1].strip() if ":" in line else line
                    state = raw_state.split()[1] if len(raw_state.split()) > 1 else raw_state
                    svc["state"] = state
                elif line.startswith("DISPLAY_NAME:"):
                    svc["display"] = line.split(":", 1)[1].strip()
                    if svc.get("name"):
                        count += 1
                        running = svc.get("state","") == "RUNNING"
                        sc = f"[green]▶ RUNNING[/green]" if running else f"[red]■ {svc.get('state','?')}[/red]"
                        t_ui.add_row(svc.get("name","?")[:30], sc, "win32", "—",
                                     svc.get("display","?")[:28])
                    svc = {}
            info(f"{count} services listés.")
        except Exception as e:
            error(f"Erreur : {e}")

    else:
        # Linux — systemctl ou /etc/init.d
        try:
            result = subprocess.run(
                ["systemctl", "list-units", "--type=service", "--all",
                 "--no-pager", "--plain", "--no-legend"],
                capture_output=True, text=True, timeout=10
            )
            count = 0
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) < 4: continue
                name, load, active, sub = parts[0], parts[1], parts[2], parts[3]
                desc = " ".join(parts[4:])[:28] if len(parts) > 4 else "—"

                if active == "active":
                    status_str = f"[green]▶ active[/green]"
                elif active == "failed":
                    status_str = f"[red]✘ failed[/red]"
                elif active == "inactive":
                    status_str = f"[dim]■ inactive[/dim]"
                else:
                    status_str = f"[yellow]{active}[/yellow]"

                # Trouver le PID
                pid_str = "—"
                try:
                    pid_res = subprocess.run(
                        ["systemctl", "show", name, "--property=MainPID"],
                        capture_output=True, text=True, timeout=2
                    )
                    for l2 in pid_res.stdout.splitlines():
                        if l2.startswith("MainPID="):
                            pid_val = l2.split("=")[1].strip()
                            if pid_val and pid_val != "0": pid_str = pid_val
                except Exception: pass

                t_ui.add_row(name[:30], status_str, sub[:10], pid_str, desc)
                count += 1

            if count == 0:
                # Fallback : lire /etc/init.d
                init_d = "/etc/init.d"
                if os.path.isdir(init_d):
                    for svc_name in sorted(os.listdir(init_d))[:40]:
                        t_ui.add_row(svc_name, "[dim]—[/dim]", "init.d", "—", "—")
                        count += 1

            info(f"{count} service(s) trouvé(s).")
        except FileNotFoundError:
            error("systemctl non disponible. Ce système n'utilise pas systemd.")
        except subprocess.TimeoutExpired:
            error("Timeout — trop de services à lister.")

    console.print(t_ui)

    # Action optionnelle
    console.print()
    action_svc = console.input(
        f"[{col}]  Nom de service à inspecter [dim](vide = ignorer)[/dim] ❯ [/{col}]"
    ).strip()
    if action_svc:
        try:
            res = subprocess.run(
                ["systemctl", "status", action_svc, "--no-pager"],
                capture_output=True, text=True, timeout=5
            )
            console.print()
            console.print(Rule(f"[{col}]status : {action_svc}[/{col}]", style=f"dim {col}"))
            console.print(res.stdout or res.stderr)
        except Exception:
            try:
                res2 = subprocess.run(
                    ["sc", "query", action_svc],
                    capture_output=True, text=True, timeout=5
                )
                console.print(res2.stdout)
            except Exception as e2:
                error(str(e2))


# ── 33 · ENV INSPECTOR ──────────────────────────────────
def env_inspector():
    """Affiche et filtre les variables d'environnement."""
    col = th()["primary"]

    SENSITIVE = {"password","passwd","secret","token","key","api_key","apikey",
                 "auth","credential","private","cert","ssl","pass","pwd"}

    filtr = console.input(
        f"[{col}]  Filtre [dim](vide = tout afficher)[/dim] ❯ [/{col}]"
    ).strip().lower()

    t_ui = themed_table(border_style=col)
    t_ui.add_column("Variable", style=col, width=30)
    t_ui.add_column("Valeur",   style="white", width=56)

    count = 0
    for key, val in sorted(os.environ.items()):
        if filtr and filtr not in key.lower() and filtr not in val.lower():
            continue
        # Masquer les valeurs sensibles
        is_sensitive = any(s in key.lower() for s in SENSITIVE)
        display_val = f"[red]{'*' * min(len(val), 20)}  [dim](masqué)[/dim][/red]" if is_sensitive else val[:56]
        t_ui.add_row(key, display_val)
        count += 1

    console.print(t_ui)
    info(f"{count} variable(s) affichée(s).")
    if any(any(s in k.lower() for s in SENSITIVE) for k in os.environ):
        warn("Des variables sensibles ont été masquées (tokens, mots de passe...).")


# ── 34 · ARP TABLE ──────────────────────────────────────
def arp_table():
    """Affiche la table ARP locale et signale les doublons d'IP."""
    col = th()["primary"]

    t_ui = themed_table(border_style=col)
    t_ui.add_column("IP",        style=col, width=20)
    t_ui.add_column("MAC",       style="bold white", width=22)
    t_ui.add_column("Interface", style="dim", width=14)
    t_ui.add_column("Type",      style="dim", width=10)
    t_ui.add_column("Alerte",    width=14)

    entries = []

    if platform.system().lower() == "windows":
        try:
            res = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5)
            iface = "?"
            for line in res.stdout.splitlines():
                line = line.strip()
                if line.startswith("Interface:"):
                    iface = line.split()[1]
                elif "dynamic" in line.lower() or "static" in line.lower():
                    parts = line.split()
                    if len(parts) >= 3:
                        entries.append({"ip": parts[0], "mac": parts[1],
                                        "type": parts[2], "iface": iface})
        except Exception as e: error(str(e)); return
    else:
        try:
            res = subprocess.run(["arp", "-n"], capture_output=True, text=True, timeout=5)
            for line in res.stdout.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 3 and parts[2] != "(incomplete)":
                    entries.append({"ip": parts[0], "mac": parts[2],
                                    "type": "dynamic", "iface": parts[-1] if len(parts) >= 5 else "?"})
        except FileNotFoundError:
            # Fallback : lire /proc/net/arp
            try:
                with open("/proc/net/arp", "r") as f:
                    lines = f.readlines()[1:]
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 6 and parts[3] != "00:00:00:00:00:00":
                        entries.append({"ip": parts[0], "mac": parts[3],
                                        "type": "dynamic", "iface": parts[5]})
            except Exception as e: error(str(e)); return

    # Détection doublons MAC
    mac_count: dict = {}
    for e in entries:
        mac_count[e["mac"]] = mac_count.get(e["mac"], 0) + 1

    dupes = 0
    for e in entries:
        is_dupe = mac_count.get(e["mac"], 1) > 1
        alerte = "[red]⚠ ARP SPOOF?[/red]" if is_dupe else "[green]OK[/green]"
        if is_dupe: dupes += 1
        t_ui.add_row(e["ip"], e["mac"], e.get("iface","?"), e["type"], alerte)

    console.print(t_ui)
    info(f"{len(entries)} entrée(s) ARP.")
    if dupes:
        warn(f"{dupes} doublon(s) MAC détecté(s) — possible ARP poisoning/spoofing !")
    else:
        success("Aucun doublon MAC détecté.")


# ── 35 · NET CONNECTIONS ────────────────────────────────
def net_connections():
    """Liste les connexions réseau actives groupées par état."""
    col = th()["primary"]

    t_ui = themed_table(border_style=col)
    t_ui.add_column("Proto",     style=col, width=8)
    t_ui.add_column("Local",     style="white", width=24)
    t_ui.add_column("Distant",   style="white", width=24)
    t_ui.add_column("État",      width=14)
    t_ui.add_column("PID",       style="dim", width=8)
    t_ui.add_column("Process",   style="dim", width=18)

    STATE_COLORS = {
        "ESTABLISHED": "green", "LISTEN": "cyan", "TIME_WAIT": "yellow",
        "CLOSE_WAIT": "yellow", "FIN_WAIT1": "dim", "FIN_WAIT2": "dim",
        "SYN_SENT": "magenta", "SYN_RECV": "magenta", "NONE": "dim",
    }

    stats: dict = {}
    rows = []

    try:
        conns = psutil.net_connections(kind="all")
    except psutil.AccessDenied:
        warn("Accès limité — lancez en root pour voir toutes les connexions.")
        try:
            conns = psutil.net_connections(kind="inet")
        except Exception as e:
            error(str(e)); return

    for c in conns:
        status = getattr(c, "status", "NONE") or "NONE"
        stats[status] = stats.get(status, 0) + 1

        laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "—"
        raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "—"
        proto = "TCP" if c.type == socket.SOCK_STREAM else "UDP"

        pid_str, proc_name = str(c.pid or "—"), "—"
        if c.pid:
            try:
                proc_name = psutil.Process(c.pid).name()[:18]
            except (psutil.NoSuchProcess, psutil.AccessDenied): pass

        sc = STATE_COLORS.get(status, "white")
        rows.append((proto, laddr, raddr, f"[{sc}]{status}[/{sc}]", pid_str, proc_name))

    # Trier : ESTABLISHED en premier
    order = ["ESTABLISHED","LISTEN","SYN_SENT","SYN_RECV","TIME_WAIT",
             "CLOSE_WAIT","FIN_WAIT1","FIN_WAIT2","NONE"]
    rows.sort(key=lambda r: (order.index(r[3].split("]")[1].split("[")[0]) 
                              if any(s in r[3] for s in order) else 99, r[1]))

    for row in rows:
        t_ui.add_row(*row)

    console.print(t_ui)
    console.print()

    # Résumé par état
    summary = themed_table(border_style=col, show_header=False)
    summary.add_column("État",  style=col, width=16)
    summary.add_column("Nb",    style="bold white", width=6)
    for st, nb in sorted(stats.items(), key=lambda x: -x[1]):
        sc = STATE_COLORS.get(st, "white")
        summary.add_row(f"[{sc}]{st}[/{sc}]", str(nb))
    console.print(Align.center(summary))
    info(f"{len(rows)} connexion(s) au total.")


# ── 36 · FILE HASHER ────────────────────────────────────
def file_hasher():
    """Calcule les hash MD5/SHA256/SHA512 d'un fichier local."""
    col = th()["primary"]

    filepath = console.input(f"[{col}]  Chemin du fichier ❯ [/{col}]").strip()

    # Expansion ~ et variables
    filepath = os.path.expanduser(os.path.expandvars(filepath))

    if not os.path.isfile(filepath):
        error(f"Fichier introuvable : {filepath}")
        return

    size = os.path.getsize(filepath)
    info(f"Fichier : {filepath}  ({size/1e6:.2f} MB)")

    algos = {
        "MD5":      hashlib.md5(),
        "SHA1":     hashlib.sha1(),
        "SHA256":   hashlib.sha256(),
        "SHA512":   hashlib.sha512(),
        "SHA3-256": hashlib.sha3_256(),
        "BLAKE2b":  hashlib.blake2b(),
    }

    console.print(f"[dim {col}]  Calcul en cours...[/dim {col}]")
    start = time.time()

    try:
        with open(filepath, "rb") as f:
            chunk_size = 65536
            while chunk := f.read(chunk_size):
                for h in algos.values():
                    h.update(chunk)
    except PermissionError:
        error(f"Accès refusé à {filepath}")
        return
    except Exception as e:
        error(str(e))
        return

    elapsed = time.time() - start

    t_ui = themed_table(border_style=col)
    t_ui.add_column("Algo",     style=col, width=12)
    t_ui.add_column("Hash",     style="bold white", width=70)

    for name, h in algos.items():
        t_ui.add_row(name, h.hexdigest())

    console.print(t_ui)

    # Vérification optionnelle
    console.print()
    ref_hash = console.input(
        f"[{col}]  Hash de référence à comparer [dim](vide = ignorer)[/dim] ❯ [/{col}]"
    ).strip().lower()

    if ref_hash:
        found = False
        for name, h in algos.items():
            if h.hexdigest() == ref_hash:
                success(f"Correspondance {name} ! Le fichier est intègre. ✔")
                found = True
                break
        if not found:
            error("Aucun hash ne correspond — fichier potentiellement corrompu ou altéré !")

    info(f"Calculé en {elapsed:.2f}s  ({size/1e6/elapsed:.1f} MB/s)")


# ── 37 · CRON INSPECTOR ─────────────────────────────────
def cron_inspector():
    """Affiche les tâches cron de l'utilisateur et du système."""
    col = th()["primary"]
    system = platform.system().lower()

    if system == "windows":
        console.print(f"[dim {col}]  Windows — récupération des tâches planifiées (schtasks)...[/dim {col}]\n")
        try:
            res = subprocess.run(
                ["schtasks", "/query", "/fo", "LIST", "/v"],
                capture_output=True, text=True, timeout=15
            )
            t_ui = themed_table(border_style=col)
            t_ui.add_column("Tâche",    style="bold white", width=40)
            t_ui.add_column("Statut",   width=14)
            t_ui.add_column("Dernière", style="dim", width=22)
            t_ui.add_column("Prochaine",style="dim", width=22)

            task = {}
            count = 0
            for line in res.stdout.splitlines():
                line = line.strip()
                if line.startswith("TaskName:"):
                    task["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("Status:"):
                    task["status"] = line.split(":", 1)[1].strip()
                elif line.startswith("Last Run Time:"):
                    task["last"] = line.split(":", 1)[1].strip()
                elif line.startswith("Next Run Time:"):
                    task["next"] = line.split(":", 1)[1].strip()
                    if task.get("name"):
                        count += 1
                        st = task.get("status","?")
                        sc = "green" if "Running" in st or "Ready" in st else "dim"
                        t_ui.add_row(task.get("name","?")[:40],
                                     f"[{sc}]{st}[/{sc}]",
                                     task.get("last","?")[:22],
                                     task.get("next","?")[:22])
                    task = {}

            console.print(t_ui)
            info(f"{count} tâche(s) planifiée(s) trouvée(s).")
        except FileNotFoundError:
            error("schtasks non disponible.")
        except subprocess.TimeoutExpired:
            error("Timeout lors de la récupération des tâches.")
        return

    # ── Linux / macOS ──
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Source",   style=col, width=22)
    t_ui.add_column("Schedule", style="bold white", width=22)
    t_ui.add_column("Commande", style="white", width=42)

    count = 0

    # 1. crontab de l'utilisateur courant
    try:
        res = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            for line in res.stdout.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split(None, 5)
                    if len(parts) >= 6:
                        schedule = " ".join(parts[:5])
                        command  = parts[5][:42]
                    else:
                        schedule = line[:20]; command = line[20:62]
                    t_ui.add_row(f"[dim]crontab (user)[/dim]", schedule, command)
                    count += 1
        elif "no crontab" in (res.stderr or "").lower():
            t_ui.add_row("[dim]crontab (user)[/dim]", "[dim]—[/dim]", "[dim]Vide[/dim]")
    except FileNotFoundError:
        t_ui.add_row("[dim]crontab[/dim]", "[red]indisponible[/red]", "—")

    # 2. Fichiers cron système
    CRON_DIRS = [
        "/etc/cron.d", "/etc/cron.daily", "/etc/cron.hourly",
        "/etc/cron.weekly", "/etc/cron.monthly"
    ]

    for cron_dir in CRON_DIRS:
        if not os.path.isdir(cron_dir): continue
        short_dir = os.path.basename(cron_dir)
        for fname in sorted(os.listdir(cron_dir)):
            fpath = os.path.join(cron_dir, fname)
            if not os.path.isfile(fpath): continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and not line.startswith("PATH"):
                            parts = line.split(None, 6)
                            if len(parts) >= 6:
                                schedule = " ".join(parts[:5])
                                command  = " ".join(parts[5:])[:42]
                                t_ui.add_row(f"[dim]{short_dir}/{fname}[/dim]", schedule, command)
                                count += 1
            except PermissionError:
                t_ui.add_row(f"[dim]{short_dir}/{fname}[/dim]", "[red]accès refusé[/red]", "—")

    # 3. /etc/crontab
    if os.path.isfile("/etc/crontab"):
        try:
            with open("/etc/crontab", "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("PATH") \
                       and not line.startswith("SHELL") and not line.startswith("HOME"):
                        parts = line.split(None, 7)
                        if len(parts) >= 7:
                            schedule = " ".join(parts[:5])
                            command  = " ".join(parts[6:])[:42]
                            t_ui.add_row("[dim]/etc/crontab[/dim]", schedule, command)
                            count += 1
        except PermissionError:
            t_ui.add_row("[dim]/etc/crontab[/dim]", "[red]accès refusé[/red]", "—")

    if count == 0:
        t_ui.add_row("—", "[dim]Aucune tâche trouvée[/dim]", "—")

    console.print(t_ui)
    info(f"{count} tâche(s) cron trouvée(s).")
    if not is_admin():
        info("Lancez en root pour voir toutes les crontabs système.")


# ═══════════════════════════════════════════════════════
#  ROUTER
# ═══════════════════════════════════════════════════════
ACTIONS = {
    # Système
    "01": system_info,  "1": system_info,
    "02": cpu_info,     "2": cpu_info,
    "03": ram_info,     "3": ram_info,
    "04": disk_info,    "4": disk_info,
    "05": uptime_info,  "5": uptime_info,
    "06": export_sys,   "6": export_sys,
    # Réseau
    "07": network_info, "7": network_info,
    "08": ping_test,    "8": ping_test,
    "09": net_stats,    "9": net_stats,
    "10": dns_lookup,
    "11": port_checker,
    "12": scan_lan,
    # Monitoring
    "13": live_monitor,
    "14": top_processes,
    # Utilitaires
    "15": hash_gen,
    "16": password_gen,
    "17": pass_checker,
    "18": base64_tool,
    "19": clean_temp,
    # Avancé
    "20": toggle_lang,
    "21": traceroute,
    "22": whois_geoip,
    "23": qr_ascii,
    "24": converter,
    "25": suspicious_processes,
    "26": speedtest_basic,
    "27": change_theme,
    "28": show_history,
    # ── NOUVEAU v4.1 ──
    "29": firewall_rules,
    "30": ssh_audit,
    "31": watcher_logs,
    "32": services_manager,
    "33": env_inspector,
    "34": arp_table,
    "35": net_connections,
    "36": file_hasher,
    "37": cron_inspector,
}

# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════
def main():
    while True:
        banner()
        choice = draw_menu()

        if choice in ("00","0","quit","q","exit"):
            clr()
            console.print(f"\n{Align.center(f'[bold {th()['primary']}]{t('bye')}[/bold {th()['primary']}]')}\n")
            break

        fn = ACTIONS.get(choice)
        if fn:
            if choice in ("20", "27"):
                fn(); continue
            label, color = _color_for(choice)
            section(label, color)
            fn()
        else:
            console.print(f"  [{th()['danger']}]{t('err')}[/{th()['danger']}]")
            time.sleep(0.6)
            continue
        pause()

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: clr(); sys.exit(0)
