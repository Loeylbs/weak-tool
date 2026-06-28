#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  ██████╗ ██████╗ ██╗███╗   ███╗███████╗
  ██╔══██╗██╔══██╗██║████╗ ████║██╔════╝
  ██████╔╝██████╔╝██║██╔████╔██║█████╗
  ██╔═══╝ ██╔══██╗██║██║╚██╔╝██║██╔══╝
  ██║     ██║  ██║██║██║ ╚═╝ ██║███████╗
  ╚═╝     ╚═╝  ╚═╝╚═╝╚═╝     ╚═╝╚══════╝

  PRIME TOOL v4.0.1 — Multi-Tool Terminal UPGRADED (Corrected)
  Nouveautés : Thèmes, Traceroute, Whois, QR ASCII, Convertisseur,
               Processus suspects, Speedtest, Historique commandes, UI améliorée.
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
VERSION      = "v4.0.1"
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
            "c_uti": "UTILITAIRES", "c_adv": "AVANCÉ",
            "sys1": "Info Système", "sys2": "Statut CPU", "sys3": "Info RAM",
            "sys4": "Info Disque", "sys5": "Uptime / Boot", "sys6": "Exporter Rapport",
            "net1": "Info Réseau", "net2": "Test Ping", "net3": "Stats Réseau",
            "net4": "Lookup DNS", "net5": "Check Ports", "net6": "Scan LAN",
            "mon1": "Moniteur Live", "mon2": "Top Processus",
            "uti1": "Hash Generator", "uti2": "Générateur Mdp", "uti3": "Testeur Mdp",
            "uti4": "Outil Base64", "uti5": "Nettoyer Temp",
            "adv1": "Traceroute", "adv2": "Whois / GeoIP", "adv3": "QR Code ASCII",
            "adv4": "Convertisseur", "adv5": "Proc. Suspects", "adv6": "Speedtest",
            "theme": "Changer Thème", "hist": "Historique", "lang": "Langue (FR/EN)",
            "quit": "[ QUITTER ]", "prompt": "  ❯ ", "bye": "À plus !",
            "err": "Choix invalide.", "pause": "  ↵ Entrée pour continuer..."
        },
        "en": {
            "c_sys": "SYSTEM", "c_net": "NETWORK", "c_mon": "MONITORING",
            "c_uti": "UTILITIES", "c_adv": "ADVANCED",
            "sys1": "System Info", "sys2": "CPU Status", "sys3": "RAM Info",
            "sys4": "Disk Info", "sys5": "Uptime / Boot", "sys6": "Export Report",
            "net1": "Network Info", "net2": "Ping Test", "net3": "Net Stats",
            "net4": "DNS Lookup", "net5": "Port Checker", "net6": "LAN Scanner",
            "mon1": "Live Monitor", "mon2": "Top Processes",
            "uti1": "Hash Generator", "uti2": "Password Gen", "uti3": "Pass Checker",
            "uti4": "Base64 Tool", "uti5": "Clean Temp",
            "adv1": "Traceroute", "adv2": "Whois / GeoIP", "adv3": "ASCII QR Code",
            "adv4": "Converter", "adv5": "Susp. Procs", "adv6": "Speedtest",
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
#  FEATURES SYSTÈME
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
#  FEATURES RÉSEAU
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
            pub_ip, geo_loc, org = data.get("ip", "?"), f"{data.get('city','?')}, {data.get('region','?')}, {data.get('country','?')}", data.get("org", "?")
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
    known = { 21:"FTP", 22:"SSH", 23:"Telnet", 25:"SMTP", 53:"DNS", 80:"HTTP", 110:"POP3", 143:"IMAP", 443:"HTTPS", 3306:"MySQL", 3389:"RDP", 5432:"PgSQL", 8080:"HTTP-Alt", 27017:"MongoDB" }
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
#  FEATURES MONITORING
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
            ul_rate, dl_rate = (net_cur.bytes_sent - net_prev.bytes_sent) / delta / 1024, (net_cur.bytes_recv - net_prev.bytes_recv) / delta / 1024
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
            
            top_cpu = sorted(psutil.process_iter(["name","cpu_percent"]), key=lambda p: p.info.get("cpu_percent") or 0, reverse=True)[:3]
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
        cpu, ram = p.get("cpu_percent") or 0, (p.get("memory_info").rss / 1e6) if p.get("memory_info") else 0
        name, user = (p.get("name") or "?")[:24], (p.get("username") or "?")[:14]
        t_ui.add_row(str(p["pid"]), name, user, p.get("status","?"), f"{cpu:.1f}%", f"{ram:.0f} MB", pct_bar(min(cpu,100)))
    console.print(t_ui)

# ═══════════════════════════════════════════════════════
#  FEATURES UTILITAIRES
# ═══════════════════════════════════════════════════════

def hash_gen():
    col  = th()["cat_uti"]
    text = console.input(f"[{col}]  Texte ❯ [/{col}]")
    enc  = text.encode()
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Algo", style=col, width=10)
    t_ui.add_column("Résultat", style="white", width=70)
    t_ui.add_row("MD5", hashlib.md5(enc).hexdigest())
    t_ui.add_row("SHA1", hashlib.sha1(enc).hexdigest())
    t_ui.add_row("SHA256", hashlib.sha256(enc).hexdigest())
    t_ui.add_row("SHA512", hashlib.sha512(enc).hexdigest())
    t_ui.add_row("SHA3-256", hashlib.sha3_256(enc).hexdigest())
    console.print(t_ui)

def password_gen():
    col = th()["cat_uti"]
    try: n = int(console.input(f"[{col}]  Longueur [dim](default 18)[/dim] ❯ [/{col}]") or "18")
    except ValueError: n = 18

    sets = {"alpha": string.ascii_letters, "digits": string.digits, "spec": "!@#$%^&*()-_=+[]{}|;:,.<>?"}
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
        pwd = random.choice(sets["alpha"].upper()) + random.choice(sets["digits"]) + random.choice(sets["spec"]) + ''.join(random.choice(chars) for _ in range(n - 3))
        pwd_list = list(pwd); random.shuffle(pwd_list); pwd = ''.join(pwd_list)
        sc = strength(pwd)
        t_ui.add_row(str(i+1), pwd, f"{pct_bar(sc, 10)} {sc}/100")
    console.print(t_ui)

def pass_checker():
    col = th()["cat_uti"]
    pwd = console.input(f"[{col}]  Mot de passe à tester ❯ [/{col}]")
    score = 0
    criteria = [
        ("Longueur ≥ 8", len(pwd) >= 8, 20), ("Longueur ≥ 12", len(pwd) >= 12, 20),
        ("Majuscules", any(c.isupper() for c in pwd), 15), ("Minuscules", any(c.islower() for c in pwd), 15),
        ("Chiffres", any(c.isdigit() for c in pwd), 15), ("Caractères spéciaux", any(c in string.punctuation for c in pwd), 15),
    ]
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Critère", style="white", width=30)
    t_ui.add_column("Statut", width=15)
    t_ui.add_column("Points", style="dim", width=10)
    
    for label, ok, pts in criteria:
        if ok: score += pts
        t_ui.add_row(label, f"[green]✔[/green]" if ok else f"[red]✘[/red]", f"+{pts}" if ok else "[dim]0[/dim]")
    t_ui.add_row("─"*28, "─"*13, "─"*8)
    lvl = "FAIBLE" if score < 40 else "MOYEN" if score < 70 else "FORT" if score < 90 else "EXCELLENT"
    lvl_col = "red" if score < 40 else "yellow" if score < 70 else "green" if score < 90 else "bright_green"
    t_ui.add_row("Score Global", f"[{lvl_col}]{lvl}[/{lvl_col}]", f"[bold]{score}/100[/bold]")
    t_ui.add_row("", f"{pct_bar(score, 14)}", "")
    console.
