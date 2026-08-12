#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  ██████╗ ██████╗ ██╗███╗   ███╗███████╗
  ██╔══██╗██╔══██╗██║████╗ ████║██╔════╝
  ██████╔╝██████╔╝██║██╔████╔██║█████╗
  ██╔═══╝ ██╔══██╗██║██║╚██╔╝██║██╔══╝
  ██║     ██║  ██║██║██║ ╚═╝ ██║███████╗
  ╚═╝     ╚═╝  ╚═╝╚═╝╚═╝     ╚═╝╚══════╝

  Multi-Tool Terminal v1.3.0 — UPGRADED (nom personnalisable, voir menu)
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
import csv
import io
import concurrent.futures
import ipaddress
import tempfile
from datetime import datetime, timedelta
from urllib.error import URLError, HTTPError
from collections import deque

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── AUTO-INSTALL ──────────────────────────────────────────
def _ensure(*pkgs):
    for p in pkgs:
        try:
            __import__(p)
        except ImportError:
            print(f"  [*] Installation de {p}...")
            subprocess.run([sys.executable, "-m", "pip", "install", p, "-q"],
                           capture_output=True)

_ensure("rich", "psutil", "pyfiglet", "qrcode")

from rich.console import Console, Group
from rich.panel   import Panel
from rich.table   import Table
from rich.text    import Text
from rich.rule    import Rule
from rich.align   import Align
from rich.live    import Live
from rich         import box
import psutil
import pyfiglet
import qrcode

console = Console()

# ── CONFIG ───────────────────────────────────────────────
TOOL_NAME    = "weak-tool"
VERSION      = "v1.3.0"
LANG         = "fr"
CMD_HISTORY  = deque(maxlen=20)
MENU_ANIM_DELAY = 0.08
MENU_ANIM_COLORS = [
    "bright_magenta", "magenta", "bright_cyan", "cyan",
    "bright_yellow", "yellow", "bright_green", "green",
    "bright_blue", "blue", "bright_red", "red",
]

# ── AUTO-UPDATE (GitHub Releases) ─────────────────────────
GITHUB_REPO          = "Loeylbs/weak-tool"  
UPDATE_CHECK_TIMEOUT = 5                     
UPDATE_DL_TIMEOUT    = 20                   
UPDATE_CONFIG_PATH   = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), f".{TOOL_NAME}_update.json"
)
NAME_CONFIG_PATH     = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), f".{TOOL_NAME}_name.json"
)

# ── THÈMES ───────────────────────────────────────────────
THEMES = {
    "neon": {
        "name": "Neon Board", "primary": "bright_cyan", "secondary": "bright_magenta",
        "accent": "bright_yellow", "danger": "bright_red", "success": "bright_green",
        "warning": "bright_yellow", "dim_col": "bright_black", "border": "bright_cyan",
        "cat_sys": "bright_yellow", "cat_net": "bright_green", "cat_mon": "bright_cyan",
        "cat_uti": "bright_magenta", "cat_adv": "bright_red",
        "dots": ". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .",
        "box": box.ASCII,
    },
    "graffiti": {
        "name": "Graffiti (Spray)", "primary": "bright_magenta", "secondary": "bright_cyan",
        "accent": "bright_yellow", "danger": "bright_red", "success": "bright_green",
        "warning": "bright_yellow", "dim_col": "magenta", "border": "bright_magenta",
        "cat_sys": "bright_yellow", "cat_net": "bright_cyan", "cat_mon": "bright_magenta",
        "cat_uti": "bright_green", "cat_adv": "bright_red",
        "dots": "▄▀▄▀▄ ░▒▓█▓▒░ ▄▀▄▀▄ ░▒▓█▓▒░ ▄▀▄▀▄ ░▒▓█▓▒░ ▄▀▄▀▄",
        "box": box.HEAVY,
    },
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
    "dracula": {
        "name": "Dracula", "primary": "bright_magenta", "secondary": "purple4",
        "accent": "bright_cyan", "danger": "red", "success": "bright_green",
        "warning": "yellow", "dim_col": "grey62", "border": "purple4",
        "cat_sys": "bright_yellow", "cat_net": "bright_green", "cat_mon": "bright_cyan",
        "cat_uti": "bright_magenta", "cat_adv": "red",
        "dots": "◈ ◇ ◈ ◇ ◈ ◇ ◈ ◇ ◈ ◇ ◈ ◇ ◈ ◇ ◈ ◇ ◈ ◇ ◈ ◇ ◈ ◇ ◈ ◇ ◈ ◇ ◈ ◇ ◈ ◇ ◈ ◇ ◈ ◇",
        "box": box.DOUBLE,
    },
    "blue-magic": {
        "name": "Blue_marine", "primary": "bright_cyan", "secondary": "blue",
        "accent": "bright_magenta", "danger": "red", "success": "bright_green",
        "warning": "yellow", "dim_col": "bright_black", "border": "cyan",
        "cat_sys": "bright_magenta", "cat_net": "green", "cat_mon": "cyan",
        "cat_uti": "blue", "cat_adv": "bright_red",
        "dots": "·  · · ·  · ·  · · ·  ·  · · ·  · ·  · · ·  ·  · · ·  · ·  · · ·  ·",
        "box": box.SQUARE,
    },
}
THEME_NAMES = list(THEMES.keys())
CURRENT_THEME_IDX = THEME_NAMES.index("blue-magic")

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
        "uti1": "Générateur de Hash", "uti2": "Générateur Mdp", "uti3": "Testeur Mdp",
        "uti4": "Outil Base64", "uti5": "Nettoyer Temp",
        "adv1": "Traceroute", "adv2": "Whois / GeoIP", "adv3": "QR Code ASCII",
        "adv4": "Convertisseur", "adv5": "Proc. Suspects", "adv6": "Speedtest",
        "new1": "Règles Pare-feu", "new2": "Audit SSH",
        "new3": "Observateur de Logs", "new4": "Gestionnaire Services",
        "new5": "Inspecteur d'Env", "new6": "Table ARP",
        "new7": "Connexions Réseau", "new8": "Hash de Fichier",
        "new9": "Inspecteur Cron", "new10": "Calcul de Sous-réseau",
        "new11": "Recherche MAC", "new12": "Personnaliser Pseudo",
        "new13": "Diskpart Simplifié",
        "new14": "Outils Texte", "new15": "Date & Heure",
        "new16": "Outils Couleur", "new17": "Encodeurs",
        "new18": "Générateur Aléatoire", "new19": "Comparateur",
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
        "new1": "Firewall Rules", "new2": "SSH Audit",
        "new3": "Log Watcher", "new4": "Services Manager",
        "new5": "Env Inspector", "new6": "ARP Table",
        "new7": "Net Connections", "new8": "File Hasher",
        "new9": "Cron Inspector", "new10": "Subnet Calc",
        "new11": "MAC Lookup", "new12": "Rename Tool",
        "new13": "Simple Diskpart",
        "new14": "Text Tools", "new15": "Date & Time",
        "new16": "Color Tools", "new17": "Encoders",
        "new18": "Random Generator", "new19": "Diff Checker",
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
    pct = max(0, min(100, pct))
    filled = max(0, int(pct / 100 * width))
    if theme_colors and THEME_NAMES[CURRENT_THEME_IDX] in ("matrix", "blood", "graffiti"):
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
    kwargs.setdefault("row_styles", ["", "dim"])
    return Table(*args, **kwargs)

def success(msg):
    console.print(f"  [{th()['success']}]✔ {msg}[/{th()['success']}]")

def error(msg):
    console.print(f"  [{th()['danger']}]✘ {msg}[/{th()['danger']}]")

def info(msg):
    console.print(f"  [{th()['secondary']}]ℹ {msg}[/{th()['secondary']}]")

def warn(msg):
    console.print(f"  [{th()['warning']}]⚠ {msg}[/{th()['warning']}]")

# ── AUTO-UPDATE ────────────────────────────────────────────
def _load_update_config():
    try:
        with open(UPDATE_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_update_config(data):
    try:
        with open(UPDATE_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

# ── NOM PERSONNALISÉ (pseudo) ─────────────────────────────
def _load_display_name():
    try:
        with open(NAME_CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = (json.load(f).get("display_name") or "").strip()
            return saved if saved else TOOL_NAME
    except Exception:
        return TOOL_NAME

def _save_display_name(name):
    try:
        with open(NAME_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"display_name": name}, f, indent=2)
        return True
    except Exception:
        return False

DISPLAY_NAME = _load_display_name()

def _parse_version(v):
    v = v.lstrip("vV")
    parts = []
    for chunk in v.split("."):
        num = ""
        for ch in chunk:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])

def _is_newer(remote, local):
    try:
        return _parse_version(remote) > _parse_version(local)
    except Exception:
        return False

def _is_developer_version(local, remote):
    try:
        return _parse_version(local) > _parse_version(remote)
    except Exception:
        return False

def _fetch_latest_release():
    if GITHUB_REPO == "Loeylbs/weak-tool":
        return None
    url = f"https://api.github.com/repos/Loeylbs/weak-tool/releases/latest"
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{TOOL_NAME}-updater",
    })
    try:
        with urllib.request.urlopen(req, timeout=UPDATE_CHECK_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, HTTPError, TimeoutError, ValueError, OSError):
        return None

def _pick_asset(release):
    own_name = os.path.basename(os.path.abspath(__file__))
    assets = release.get("assets") or []
    for a in assets:
        if a.get("name", "").lower() == own_name.lower():
            return a
    for a in assets:
        if a.get("name", "").lower().endswith(".py"):
            return a
    return None

def _download_with_progress(url, dest_path):
    from rich.progress import (Progress, BarColumn, DownloadColumn,
                                TransferSpeedColumn, TimeRemainingColumn)
    req = urllib.request.Request(url, headers={"User-Agent": f"{TOOL_NAME}-updater"})
    with urllib.request.urlopen(req, timeout=UPDATE_DL_TIMEOUT) as resp:
        total = int(resp.headers.get("Content-Length", 0) or 0)
        with Progress(
            "[progress.description]{task.description}",
            BarColumn(bar_width=40, style=th()["dim_col"], complete_style=th()["primary"]),
            DownloadColumn(), TransferSpeedColumn(), TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("  Telechargement...", total=total or None)
            with open(dest_path, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))

def _show_update_panel(local_v, remote_v, changelog):
    body = (changelog or "").strip() or "Aucune note de version fournie."
    if len(body) > 900:
        body = body[:900].rstrip() + "…"
    panel_text = (
        f"[bold]Version actuelle :[/bold] [dim]{local_v}[/dim]\n"
        f"[bold]Nouvelle version :[/bold] [{th()['success']}]{remote_v}[/{th()['success']}]\n\n"
        f"[bold]Notes de version :[/bold]\n{body}"
    )
    console.print(Panel(
        panel_text,
        title=f"[bold {th()['warning']}]🚀 MISE A JOUR DISPONIBLE[/bold {th()['warning']}]",
        border_style=th()["warning"],
        box=th()["box"],
    ))

def _prompt_update_choice():
    console.print()
    console.print(f"  [{th()['primary']}][1][/{th()['primary']}] Installer maintenant")
    console.print(f"  [{th()['secondary']}][2][/{th()['secondary']}] Me le rappeler plus tard (7 jours)")
    console.print(f"  [{th()['dim_col']}][3][/{th()['dim_col']}] Ignorer cette version")
    console.print()
    return console.input(f"  [{th()['accent']}]Choix >[/{th()['accent']}] ").strip()

def _relaunch():
    subprocess.Popen([sys.executable, os.path.abspath(__file__)] + sys.argv[1:])
    sys.exit(0)

def _spawn_relay_updater(new_path, target_path):
    relay_code = (
        "import os, sys, time, subprocess\n"
        f"new_path = {new_path!r}\n"
        f"target_path = {target_path!r}\n"
        f"python_exe = {sys.executable!r}\n"
        "for _ in range(20):\n"
        "    try:\n"
        "        os.replace(new_path, target_path)\n"
        "        break\n"
        "    except PermissionError:\n"
        "        time.sleep(0.5)\n"
        "else:\n"
        "    sys.exit(1)\n"
        "subprocess.Popen([python_exe, target_path])\n"
        "try:\n"
        "    os.remove(__file__)\n"
        "except OSError:\n"
        "    pass\n"
    )
    fd, relay_path = tempfile.mkstemp(suffix="_update_relay.py")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(relay_code)

    if os.name == "nt":
        subprocess.Popen([sys.executable, relay_path],
                          creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
    else:
        subprocess.Popen([sys.executable, relay_path], start_new_session=True)

def _apply_update(asset):
    script_path = os.path.abspath(__file__)
    script_dir  = os.path.dirname(script_path)
    tmp_path    = os.path.join(script_dir, f".{TOOL_NAME}_new.tmp")

    try:
        info("Telechargement de la mise a jour...")
        _download_with_progress(asset["browser_download_url"], tmp_path)
    except Exception as e:
        error(f"Echec du telechargement : {e}")
        try: os.remove(tmp_path)
        except OSError: pass
        return False

    try:
        shutil.copy2(script_path, script_path + ".bak")
    except Exception:
        pass  # sauvegarde en best-effort, ne doit jamais bloquer la MAJ

    try:
        os.replace(tmp_path, script_path)   # remplacement atomique, .py n'est pas verrouille pendant l'execution
        success("Mise a jour installee. Redemarrage...")
        time.sleep(0.8)
        _relaunch()
        return True
    except PermissionError:
        warn("Fichier verrouille, finalisation via un script relais...")
        _spawn_relay_updater(tmp_path, script_path)
        sys.exit(0)
    except Exception as e:
        error(f"Echec de l'installation : {e}")
        try: os.remove(tmp_path)
        except OSError: pass
        return False

def check_for_updates():
    cfg = _load_update_config()

    next_reminder = cfg.get("next_reminder")
    if next_reminder:
        try:
            if datetime.now() < datetime.fromisoformat(next_reminder):
                return
        except Exception:
            pass

    release = _fetch_latest_release()
    if not release or "tag_name" not in release:
        return

    remote_v = release["tag_name"]

    if _is_developer_version(VERSION, remote_v):
        info(f"Version developpeur detectee ({VERSION} > {remote_v}) : mise a jour ignoree.")
        time.sleep(1.0)
        return

    if remote_v == cfg.get("ignored_version"):
        return
    if not _is_newer(remote_v, VERSION):
        return

    asset = _pick_asset(release)
    if not asset:
        return

    clr()
    _show_update_panel(VERSION, remote_v, release.get("body", ""))
    choice = _prompt_update_choice()

    if choice == "1":
        _apply_update(asset)
    elif choice == "3":
        cfg["ignored_version"] = remote_v
        cfg.pop("next_reminder", None)
        _save_update_config(cfg)
        info("Version ignoree. (supprime le fichier .{}_update.json pour reinitialiser)".format(TOOL_NAME))
        time.sleep(1.2)
    else:
        cfg["next_reminder"] = (datetime.now() + timedelta(days=7)).isoformat()
        _save_update_config(cfg)
        info("Rappel dans 7 jours.")
        time.sleep(1.2)

# ── DÉCOR / BANNER ───────────────────────────────────────
def _gradient_banner(ascii_logo: str):
    theme_key = THEME_NAMES[CURRENT_THEME_IDX]
    lines = ascii_logo.rstrip().splitlines()

    if theme_key == "neon":
        gradient = ["bright_yellow", "bright_cyan", "bright_magenta", "bright_cyan", "bright_yellow"]
    elif theme_key == "cyber":
        gradient = ["bright_cyan","cyan","blue","bright_blue","cyan","bright_cyan"]
    elif theme_key == "matrix":
        gradient = ["bright_green","green","bright_green","green","bright_green","green"]
    elif theme_key == "blood":
        gradient = ["bright_red","red","bright_red","red","bright_red","bright_red"]
    elif theme_key == "graffiti":
        gradient = ["bright_magenta","bright_cyan","bright_yellow","bright_cyan","bright_magenta"]
    elif theme_key == "dracula":
        gradient = ["bright_magenta","purple4","bright_cyan","purple4","bright_magenta","purple4"]
    elif theme_key == "blue_marine":
        gradient = ["bright_cyan","cyan","blue","bright_blue","cyan","bright_cyan"]
    else:
        gradient = ["white","bright_white","white","bright_white","white","white"]

    for i, line in enumerate(lines):
        color = gradient[i % len(gradient)]
        console.print(Align.center(Text(line, style=f"bold {color}")))

def _screen_width():
    return max(84, min(console.width, 170))

def _neon_line(width=None):
    width = width or _screen_width()
    left = max(8, width // 5)
    center = max(12, width // 6)
    right = max(8, width - left - center - 10)
    text = Text()
    text.append(" " * 3)
    text.append(".".join([""] * left), style=th()["primary"])
    text.append("++", style=th()["secondary"])
    text.append(".".join([""] * center), style=th()["primary"])
    text.append("++", style=th()["secondary"])
    text.append(".".join([""] * right), style=th()["primary"])
    return text

def _starfield(width, rows=2):
    rng = random.Random(1337)
    chars = (".", "·", "*")
    dim, sec = th()["dim_col"], th()["secondary"]
    for _ in range(rows):
        line = Text()
        for _c in range(width):
            if rng.random() < 0.035:
                ch = rng.choice(chars)
                style = f"bold {sec}" if rng.random() < 0.3 else dim
                line.append(ch, style=style)
            else:
                line.append(" ")
        console.print(Align.center(line))

def _pixel_fade(width, rows=2, base_density=0.14):
    rng = random.Random(2026)
    pri, dim = th()["primary"], th()["dim_col"]
    for i in range(rows):
        density = base_density * (1 - i / max(1, rows))
        line = Text()
        for _c in range(width):
            if rng.random() < density:
                ch = rng.choice(("░", "▒", "·", "."))
                style = pri if rng.random() < 0.3 else dim
                line.append(ch, style=style)
            else:
                line.append(" ")
        console.print(Align.center(line))

def _anim_color():
    return th()["primary"]

def banner():
    clr()
    width = _screen_width()
    sec, dim = th()["secondary"], th()["dim_col"]
    privilege = "ADMIN" if is_admin() else "USER"
    meta = f"{VERSION} · {privilege} · {getpass.getuser()}@{platform.node()} · {datetime.now().strftime('%H:%M:%S')}"

    console.print()
    _starfield(width)

    ascii_logo = None
    for font in ("ansi_shadow", "big", "standard", "slant", "small", "mini"):
        try:
            candidate = pyfiglet.figlet_format(DISPLAY_NAME, font=font, width=width)
        except Exception:
            continue
        lines = candidate.rstrip().splitlines()
        if max((len(line) for line in lines), default=0) <= width:
            ascii_logo = candidate
            break
    if ascii_logo is None:
        ascii_logo = f"/ {DISPLAY_NAME.upper()} \\"

    _gradient_banner(ascii_logo)
    _pixel_fade(width)
    console.print(Align.center(Text(meta, style=dim)))
    console.print(Align.center(Text(f"theme:{th()['name']}", style=sec)))
    console.print()

# ── CATÉGORIES DU MENU ────────────────────────────────────
def get_cats():
    return [
        (t("c_sys"), th()["cat_sys"], [
            ("01", t("sys1")), ("02", t("sys2")), ("03", t("sys3")),
            ("04", t("sys4")), ("05", t("sys5")), ("06", t("sys6")),
            ("32", t("new4")), ("33", t("new5")), ("37", t("new9")),
            ("41", t("new13")),
        ]),
        (t("c_net"), th()["cat_net"], [
            ("07", t("net1")), ("08", t("net2")), ("09", t("net3")),
            ("10", t("net4")), ("11", t("net5")), ("12", t("net6")),
            ("29", t("new1")), ("30", t("new2")), ("34", t("new6")),
            ("35", t("new7")), ("38", t("new10")), ("39", t("new11")),
        ]),
        (t("c_mon"), th()["cat_mon"], [
            ("13", t("mon1")), ("14", t("mon2")), ("31", t("new3")),
        ]),
        (t("c_uti"), th()["cat_uti"], [
            ("15", t("uti1")), ("16", t("uti2")), ("17", t("uti3")),
            ("18", t("uti4")), ("19", t("uti5")), ("36", t("new8")),
            ("42", t("new14")), ("43", t("new15")), ("44", t("new16")),
            ("45", t("new17")), ("46", t("new18")),
        ]),
        (t("c_adv"), th()["cat_adv"], [
            ("21", t("adv1")), ("22", t("adv2")), ("23", t("adv3")),
            ("24", t("adv4")), ("25", t("adv5")), ("26", t("adv6")),
            ("27", t("theme")), ("28", t("hist")), ("20", t("lang")), ("00", t("quit")),
            ("40", t("new12")), ("47", t("new19")),
        ]),
    ]

def _make_panel(title: str, color: str, items: list, width: int = 32, border_color: str = None) -> Panel:
    border_color = border_color or color
    t_obj = Text()
    max_label = max(10, width - 10)
    for num, label in items:
        clipped = label if len(label) <= max_label else label[:max_label - 3] + "..."
        t_obj.append(f"[{num}] ", style=f"bold {border_color}")
        t_obj.append(f"{clipped}\n", style=color)
    t_obj.rstrip()
    return Panel(
        t_obj,
        title=Text(f"/ {title} \\", style=f"bold {border_color}"),
        title_align="center",
        border_style=border_color,
        box=th()["box"],
        expand=False,
        width=width,
        padding=(0, 1),
    )

# ── BORDURE TOURNANTE (spinner de chargement) ─────────────
def _spin_panel_render(title: str, color: str, items: list, width: int,
                        border_color: str, phase: int, tail: int = 5) -> Text:
    panel = _make_panel(title, color, items, width=width, border_color=border_color)
    opts = console.options.update(width=width)
    lines = console.render_lines(panel, opts, pad=False)
    h = len(lines)
    w = sum(len(seg.text) for seg in lines[0]) if lines else width

    top_len, right_len, bottom_len, left_len = w, max(0, h - 2), w, max(0, h - 2)
    perim_len = max(1, top_len + right_len + bottom_len + left_len)
    lit = {(phase + k) % perim_len for k in range(tail)}

    out = Text()
    for r, segs in enumerate(lines):
        col = 0
        for seg in segs:
            style_str = str(seg.style) if seg.style else ""
            for ch in seg.text:
                idx = None
                if r == 0 and style_str == border_color:
                    idx = col
                elif r == h - 1 and style_str == border_color:
                    idx = top_len + right_len + (w - 1 - col)
                elif col == w - 1 and 0 < r < h - 1:
                    idx = top_len + (r - 1)
                elif col == 0 and 0 < r < h - 1:
                    idx = top_len + right_len + bottom_len + (h - 2 - r)

                if idx is not None:
                    if idx in lit:
                        out.append(ch, style=f"bold {border_color}")
                    else:
                        out.append(" ")
                else:
                    out.append(ch, style=seg.style)
                col += 1
        out.append("\n")
    return out

def _spin_menu_intro(cats, width, wide, panel_w):
    borders = [th()["border"]] * len(cats)
    dim = th()["dim_col"]

    def frame(phase):
        parts = [
            Align.center(_spin_panel_render(*cats[0], panel_w, borders[0], phase)),
            Align.center(_neon_line(width)),
            Align.center(Text("· " * 24, style=dim)),
        ]
        if wide:
            grid = Table.grid(padding=(0, 1))
            grid.add_row(
                _spin_panel_render(*cats[3], panel_w, borders[3], phase),
                _spin_panel_render(*cats[2], panel_w, borders[2], phase),
                _spin_panel_render(*cats[4], panel_w, borders[4], phase),
                _spin_panel_render(*cats[1], panel_w, borders[1], phase),
            )
            parts.append(Align.center(grid))
        else:
            top = Table.grid(padding=(0, 1))
            top.add_row(
                _spin_panel_render(*cats[3], panel_w, borders[3], phase),
                _spin_panel_render(*cats[4], panel_w, borders[4], phase),
            )
            middle = Table.grid(padding=(0, 1))
            middle.add_row(
                _spin_panel_render(*cats[2], panel_w, borders[2], phase),
                _spin_panel_render(*cats[1], panel_w, borders[1], phase),
            )
            parts.append(Align.center(top))
            parts.append(Align.center(Text("· " * 24, style=dim)))
            parts.append(Align.center(middle))
        parts.append(Align.center(Text("-" * min(width - 12, 112), style=dim)))
        return Group(*parts)

    try:
        with Live(frame(0), console=console, refresh_per_second=20, transient=True) as live:
            for i in range(16):
                live.update(frame(i * 3))
                time.sleep(0.045)
    except Exception:
        pass

def _render_menu_frame(typed="", spin_intro=False):
    banner()
    cats = get_cats()
    pri, dim = th()["primary"], th()["dim_col"]
    width = _screen_width()
    wide = width >= 145
    panel_w = 31 if wide else 34
    borders = [th()["border"]] * len(cats)

    if spin_intro:
        _spin_menu_intro(cats, width, wide, panel_w)

    console.print(Align.center(_make_panel(*cats[0], width=panel_w, border_color=borders[0])))
    console.print(Align.center(_neon_line(width)))

    console.print(Align.center(Text("· " * 24, style=dim)))

    if wide:
        grid = Table.grid(padding=(0, 1))
        grid.add_row(
            _make_panel(*cats[3], width=panel_w, border_color=borders[3]),
            _make_panel(*cats[2], width=panel_w, border_color=borders[2]),
            _make_panel(*cats[4], width=panel_w, border_color=borders[4]),
            _make_panel(*cats[1], width=panel_w, border_color=borders[1]),
        )
        console.print(Align.center(grid))
    else:
        top = Table.grid(padding=(0, 1))
        top.add_row(
            _make_panel(*cats[3], width=panel_w, border_color=borders[3]),
            _make_panel(*cats[4], width=panel_w, border_color=borders[4]),
        )
        middle = Table.grid(padding=(0, 1))
        middle.add_row(
            _make_panel(*cats[2], width=panel_w, border_color=borders[2]),
            _make_panel(*cats[1], width=panel_w, border_color=borders[1]),
        )
        console.print(Align.center(top))
        console.print(Align.center(Text("· " * 24, style=dim)))
        console.print(Align.center(middle))

    console.print(Align.center(Text("-" * min(width - 12, 112), style=dim)))
    console.print()
    console.print(Align.center(Text(f"{t('prompt')}{typed}", style=f"bold {pri}")))

def _animated_menu_input():
    if os.name != "nt" or not sys.stdin.isatty():
        _render_menu_frame("", spin_intro=True)
        raw = console.input(f"[bold {th()['primary']}]{t('prompt')}[/bold {th()['primary']}]").strip()
        if raw:
            CMD_HISTORY.append(raw)
        return raw

    import msvcrt
    typed = ""
    _render_menu_frame(typed, spin_intro=True)
    while True:
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"):
                raw = typed.strip()
                if raw:
                    CMD_HISTORY.append(raw)
                return raw
            if ch == "\x03":
                raise KeyboardInterrupt
            if ch == "\x08":
                typed = typed[:-1]
            elif ch in ("\x00", "\xe0"):
                if msvcrt.kbhit():
                    msvcrt.getwch()
            elif ch.isprintable():
                typed += ch
            _render_menu_frame(typed)
        time.sleep(0.01)

def draw_menu() -> str:
    return _animated_menu_input()

def section(label: str, color: str):
    clr()
    banner()
    console.print(Align.center(Panel(
        Text(f">>> {label.upper()}", style=f"bold {color}"),
        border_style=color,
        box=th()["box"],
        expand=False,
        padding=(0, 4),
    )))
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
    safe_name = DISPLAY_NAME.replace(" ", "_") or TOOL_NAME
    filename = f"{safe_name}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        vm    = psutil.virtual_memory()
        u_inf = platform.uname()
        boot  = datetime.fromtimestamp(psutil.boot_time())
        up    = str(datetime.now() - boot).split(".")[0]
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"{'='*60}\n  {DISPLAY_NAME} {VERSION} — SYSTEM REPORT\n")
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
#  FEATURES MONITORING
# ═══════════════════════════════════════════════════════

def live_monitor():
    col = th()["cat_mon"]
    console.print(f"[dim {col}]  Ctrl+C pour arrêter[/dim {col}]\n")
    net_prev = psutil.net_io_counters()
    prev_time = time.time()
    cpu_hist = deque(maxlen=20)
    ram_hist = deque(maxlen=20)
    for p in psutil.process_iter():
        try: p.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): pass
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
            cpu_hist.append(cpu)
            ram_hist.append(ram)

            t_ui = themed_table(title=f"[dim]🟢 Live — {datetime.now().strftime('%H:%M:%S')}[/dim]", border_style=col)
            t_ui.add_column("Métrique",  style=col, width=14)
            t_ui.add_column("Barre",     style="white", width=20)
            t_ui.add_column("Valeur",    style="white", width=16)

            col_c = "green" if cpu < 60 else "yellow" if cpu < 85 else "red"
            col_r = "green" if ram < 60 else "yellow" if ram < 85 else "red"

            def sparkline(hist, width=16):
                if not hist: return " " * width
                chars = []
                for v in hist:
                    if v < 25: chars.append("▁")
                    elif v < 50: chars.append("▃")
                    elif v < 75: chars.append("▅")
                    else: chars.append("▇")
                return "".join(chars[-width:]).rjust(width)

            t_ui.add_row("CPU",     pct_bar(cpu),  f"[bold {col_c}]{cpu:.1f}%[/bold {col_c}]")
            t_ui.add_row("CPU Hist", sparkline(cpu_hist), "")
            t_ui.add_row("RAM",     pct_bar(ram),  f"[bold {col_r}]{ram:.1f}%[/bold {col_r}]")
            t_ui.add_row("RAM Hist", sparkline(ram_hist), "")
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
    # Amorçage : cpu_percent() doit être appelé une première fois pour poser un
    # point de référence, sinon psutil renvoie 0.0% pour tous les process.
    for p in psutil.process_iter():
        try: p.cpu_percent(None)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): pass
    time.sleep(0.3)

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
#  FEATURES UTILITAIRES
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
#  FEATURES AVANCÉES
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

    console.print(f"\n[dim]QR Code pour : [bold]{text[:40]}[/bold][/dim]\n", justify="center")
    pri = th()["primary"]

    try:
        qr = qrcode.QRCode(version=1, border=2)
        qr.add_data(text)
        qr.make(fit=True)
        matrix = qr.get_matrix()

        for row in matrix:
            line = ""
            for val in row:
                line += f"[bold {pri}]██[/bold {pri}]" if val else "  "
            console.print(Align.center(line))
            
    except Exception as e:
        error(f"Erreur de génération : {e}")
        
    console.print()

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
    for p in psutil.process_iter(["pid","name","username","cmdline","net_connections"]):
        try:
            info_p = p.info; name_l = (info_p.get("name") or "").lower(); reasons = []
            for s in SUSPECT_NAMES:
                if s in name_l: reasons.append(f"[yellow]nom '{s}'[/yellow]"); break
            try:
                for conn in (info_p.get("net_connections") or []):
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
#  FEATURES RÉCENTES
# ═══════════════════════════════════════════════════════

def firewall_rules():
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
        console.print(f"[dim {col}]  Récupération des règles iptables...[/dim {col}]\n")
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
            info("iptables indisponible ou accès refusé, tentative avec nftables...")
            try:
                res = subprocess.run(["nft", "list", "ruleset"], capture_output=True, text=True, timeout=8)
                if res.returncode == 0 and res.stdout.strip():
                    console.print(f"[{col}]{res.stdout}[/{col}]")
                else:
                    warn("Aucune règle firewall trouvée. Lancez en root pour un accès complet.")
            except FileNotFoundError:
                error("Ni iptables ni nftables disponibles sur ce système.")
        try:
            res_ufw = subprocess.run(["ufw", "status", "verbose"], capture_output=True, text=True, timeout=5)
            if res_ufw.returncode == 0 and res_ufw.stdout.strip():
                console.print()
                console.print(Rule(f"[{col}]UFW Status[/{col}]", style=f"dim {col}"))
                console.print(f"[{col}]{res_ufw.stdout}[/{col}]")
        except (FileNotFoundError, subprocess.TimeoutExpired): pass
    info("Utilisez les droits root/admin pour voir toutes les règles.")

def ssh_audit():
    col = th()["primary"]
    SSH_CONF_PATHS = [
        "/etc/ssh/sshd_config", "/etc/sshd_config", "C:\\ProgramData\\ssh\\sshd_config",
    ]
    conf_path = None
    for p in SSH_CONF_PATHS:
        if os.path.isfile(p):
            conf_path = p; break

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
                        if len(parts) == 2: config[parts[0]] = parts[1].strip()
        except PermissionError: warn(f"Accès refusé à {conf_path} — lancez en root.")

        t_ui.add_row(f"[dim]Fichier[/dim]", conf_path, "[dim]—[/dim]", "")
        t_ui.add_row("─"*24, "─"*22, "─"*18, "─"*18)

        score, total = 0, 0
        for param, (recommended, hint, exact) in CHECKS.items():
            val = config.get(param, "[dim]non défini[/dim]")
            raw = config.get(param, "")
            total += 1
            if exact: ok = (raw.lower() == recommended.lower())
            else:
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
        t_ui.add_row("Score SSH", f"[bold {pct_c}]{score}/{total}  ({pct}%)[/bold {pct_c}]", f"{pct_bar(pct, 12)}", "")
    else:
        t_ui.add_row("sshd_config", "[red]Introuvable[/red]", "—", "—")
        info("SSH n'est peut-être pas installé ou vous n'êtes pas sur Linux/Windows Server.")

    console.print(t_ui)

    ssh_running = False
    for p in psutil.process_iter(["name"]):
        try:
            n = (p.info.get("name") or "").lower()
            if "sshd" in n or "ssh" in n: ssh_running = True; break
        except (psutil.NoSuchProcess, psutil.AccessDenied): pass
    console.print()
    if ssh_running: success("Service sshd détecté comme actif.")
    else: info("Aucun processus sshd détecté (service arrêté ou non installé).")

def watcher_logs():
    col = th()["primary"]
    DEFAULT_LOGS = {
        "1": "/var/log/syslog", "2": "/var/log/auth.log", "3": "/var/log/kern.log",
        "4": "/var/log/nginx/access.log", "5": "/var/log/apache2/access.log",
    }
    if platform.system().lower() == "windows":
        DEFAULT_LOGS = { "1": "C:\\Windows\\Logs\\WindowsUpdate\\WindowsUpdate.log" }

    console.print(f"[{col}]  Logs disponibles :[/{col}]")
    for k, v in DEFAULT_LOGS.items():
        exists = "[green]✔[/green]" if os.path.isfile(v) else "[red]✘[/red]"
        console.print(f"  [dim]{k}[/dim]  {exists}  {v}")
    console.print()

    choice = console.input(f"[{col}]  Numéro ou chemin personnalisé ❯ [/{col}]").strip()
    log_path = DEFAULT_LOGS.get(choice, choice)

    if not os.path.isfile(log_path):
        error(f"Fichier introuvable : {log_path}"); return

    try: n_lines = int(console.input(f"[{col}]  Dernières lignes à afficher [dim](default: 20)[/dim] ❯ [/{col}]").strip() or "20")
    except ValueError: n_lines = 20

    def colorize(line: str) -> str:
        l = line.lower()
        if any(k in l for k in ("error","err","fatal","critical","crit","alert","emerg")): return f"[red]{line}[/red]"
        elif any(k in l for k in ("warn","warning")): return f"[yellow]{line}[/yellow]"
        elif any(k in l for k in ("info","notice","debug")): return f"[dim]{line}[/dim]"
        elif any(k in l for k in ("success","ok","started","ready","listening")): return f"[green]{line}[/green]"
        elif any(k in l for k in ("fail","denied","refused","invalid","unauthorized")): return f"[bold red]{line}[/bold red]"
        return line

    console.print(f"\n[dim {col}]  Watching : {log_path}  —  Ctrl+C pour arrêter[/dim {col}]\n")

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f.readlines()[-n_lines:]: console.print(f"  {colorize(line.rstrip())}")
    except PermissionError: error(f"Accès refusé à {log_path} — essayez en root."); return

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line: console.print(f"  [{th()['dim_col']}]{datetime.now().strftime('%H:%M:%S')}[/{th()['dim_col']}]  {colorize(line.rstrip())}")
                else: time.sleep(0.3)
    except KeyboardInterrupt: console.print(f"\n[{col}]  Watcher arrêté.[/{col}]")
    except PermissionError: error(f"Accès refusé.")

def services_manager():
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
            result = subprocess.run(["sc", "query", "type=", "all", "state=", "all"], capture_output=True, text=True, timeout=10)
            svc, count = {}, 0
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith("SERVICE_NAME:"): svc["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("STATE"): svc["state"] = line.split(":", 1)[1].strip().split()[1] if len(line.split(":", 1)[1].strip().split()) > 1 else line.split(":", 1)[1].strip()
                elif line.startswith("DISPLAY_NAME:"):
                    svc["display"] = line.split(":", 1)[1].strip()
                    if svc.get("name"):
                        count += 1
                        sc = f"[green]▶ RUNNING[/green]" if svc.get("state","") == "RUNNING" else f"[red]■ {svc.get('state','?')}[/red]"
                        t_ui.add_row(svc.get("name","?")[:30], sc, "win32", "—", svc.get("display","?")[:28])
                    svc = {}
            info(f"{count} services listés.")
        except Exception as e: error(f"Erreur : {e}")
    else:
        try:
            result = subprocess.run(["systemctl", "list-units", "--type=service", "--all", "--no-pager", "--plain", "--no-legend"], capture_output=True, text=True, timeout=10)
            count = 0
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) < 4: continue
                name, load, active, sub = parts[0], parts[1], parts[2], parts[3]
                desc = " ".join(parts[4:])[:28] if len(parts) > 4 else "—"
                status_str = f"[green]▶ active[/green]" if active == "active" else f"[red]✘ failed[/red]" if active == "failed" else f"[dim]■ inactive[/dim]" if active == "inactive" else f"[yellow]{active}[/yellow]"
                pid_str = "—"
                try:
                    pid_res = subprocess.run(["systemctl", "show", name, "--property=MainPID"], capture_output=True, text=True, timeout=2)
                    for l2 in pid_res.stdout.splitlines():
                        if l2.startswith("MainPID="):
                            pid_val = l2.split("=")[1].strip()
                            if pid_val and pid_val != "0": pid_str = pid_val
                except Exception: pass
                t_ui.add_row(name[:30], status_str, sub[:10], pid_str, desc)
                count += 1
            info(f"{count} service(s) trouvé(s).")
        except FileNotFoundError: error("systemctl non disponible.")
        except subprocess.TimeoutExpired: error("Timeout.")

    console.print(t_ui)
    console.print()
    action_svc = console.input(f"[{col}]  Nom de service à inspecter [dim](vide = ignorer)[/dim] ❯ [/{col}]").strip()
    if action_svc:
        try:
            res = subprocess.run(["systemctl", "status", action_svc, "--no-pager"], capture_output=True, text=True, timeout=5)
            console.print(Rule(f"[{col}]status : {action_svc}[/{col}]", style=f"dim {col}"))
            console.print(res.stdout or res.stderr)
        except Exception: pass

def env_inspector():
    col = th()["primary"]
    SENSITIVE = {"password","passwd","secret","token","key","api_key","apikey","auth","credential","private","cert","ssl","pass","pwd"}
    filtr = console.input(f"[{col}]  Filtre [dim](vide = tout afficher)[/dim] ❯ [/{col}]").strip().lower()
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Variable", style=col, width=30)
    t_ui.add_column("Valeur",   style="white", width=56)

    count = 0
    for key, val in sorted(os.environ.items()):
        if filtr and filtr not in key.lower() and filtr not in val.lower(): continue
        is_sensitive = any(s in key.lower() for s in SENSITIVE)
        display_val = f"[red]{'*' * min(len(val), 20)}  [dim](masqué)[/dim][/red]" if is_sensitive else val[:56]
        t_ui.add_row(key, display_val)
        count += 1

    console.print(t_ui)
    info(f"{count} variable(s) affichée(s).")

def arp_table():
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
                if line.startswith("Interface:"): iface = line.split()[1]
                elif "dynamic" in line.lower() or "static" in line.lower():
                    parts = line.split()
                    if len(parts) >= 3: entries.append({"ip": parts[0], "mac": parts[1], "type": parts[2], "iface": iface})
        except Exception as e: error(str(e)); return
    else:
        try:
            res = subprocess.run(["arp", "-n"], capture_output=True, text=True, timeout=5)
            for line in res.stdout.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 3 and parts[2] != "(incomplete)": entries.append({"ip": parts[0], "mac": parts[2], "type": "dynamic", "iface": parts[-1] if len(parts) >= 5 else "?"})
        except FileNotFoundError:
            # 'arp' (net-tools) est absent par défaut sur beaucoup de distributions
            # récentes : on retombe sur 'ip neigh' (iproute2), quasi toujours présent.
            try:
                res = subprocess.run(["ip", "neigh", "show"], capture_output=True, text=True, timeout=5)
                for line in res.stdout.splitlines():
                    parts = line.split()
                    if "lladdr" not in parts or not parts: continue
                    iface = parts[parts.index("dev") + 1] if "dev" in parts else "?"
                    mac   = parts[parts.index("lladdr") + 1]
                    entries.append({"ip": parts[0], "mac": mac, "type": parts[-1].lower(), "iface": iface})
            except FileNotFoundError:
                error("Ni 'arp' ni 'ip' (iproute2) ne sont disponibles sur ce système.")

    mac_count = {}
    for e in entries: mac_count[e["mac"]] = mac_count.get(e["mac"], 0) + 1

    dupes = 0
    for e in entries:
        is_dupe = mac_count.get(e["mac"], 1) > 1
        alerte = "[red]⚠ ARP SPOOF?[/red]" if is_dupe else "[green]OK[/green]"
        if is_dupe: dupes += 1
        t_ui.add_row(e["ip"], e["mac"], e.get("iface","?"), e["type"], alerte)

    console.print(t_ui)
    info(f"{len(entries)} entrée(s) ARP.")

def net_connections():
    col = th()["primary"]
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Proto",     style=col, width=8)
    t_ui.add_column("Local",     style="white", width=24)
    t_ui.add_column("Distant",   style="white", width=24)
    t_ui.add_column("État",      width=14)
    t_ui.add_column("PID",       style="dim", width=8)
    t_ui.add_column("Process",   style="dim", width=18)
    STATE_COLORS = {"ESTABLISHED": "green", "LISTEN": "cyan", "TIME_WAIT": "yellow", "CLOSE_WAIT": "yellow"}

    stats, rows = {}, []
    try: conns = psutil.net_connections(kind="all")
    except psutil.AccessDenied: conns = psutil.net_connections(kind="inet")

    for c in conns:
        status = getattr(c, "status", "NONE") or "NONE"
        stats[status] = stats.get(status, 0) + 1
        laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "—"
        raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "—"
        proto = "TCP" if c.type == socket.SOCK_STREAM else "UDP"
        pid_str, proc_name = str(c.pid or "—"), "—"
        if c.pid:
            try: proc_name = psutil.Process(c.pid).name()[:18]
            except Exception: pass
        sc = STATE_COLORS.get(status, "white")
        rows.append((proto, laddr, raddr, f"[{sc}]{status}[/{sc}]", pid_str, proc_name))

    for row in sorted(rows, key=lambda r: r[3]): t_ui.add_row(*row)
    console.print(t_ui)

def file_hasher():
    col = th()["primary"]
    filepath = console.input(f"[{col}]  Chemin du fichier ❯ [/{col}]").strip()
    filepath = os.path.expanduser(os.path.expandvars(filepath))
    if not os.path.isfile(filepath): error(f"Fichier introuvable : {filepath}"); return
    size = os.path.getsize(filepath)
    algos = { "MD5": hashlib.md5(), "SHA256": hashlib.sha256(), "SHA512": hashlib.sha512() }
    start = time.time()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                for h in algos.values(): h.update(chunk)
    except Exception as e: error(str(e)); return

    t_ui = themed_table(border_style=col)
    t_ui.add_column("Algo", style=col, width=12)
    t_ui.add_column("Hash", style="bold white", width=70)
    for name, h in algos.items(): t_ui.add_row(name, h.hexdigest())
    console.print(t_ui)

def cron_inspector():
    col = th()["primary"]
    if platform.system().lower() == "windows":
        try:
            console.print(f"[dim {col}]  Récupération des tâches planifiées...[/dim {col}]\n")
            res = subprocess.run(["schtasks", "/query", "/fo", "CSV", "/v"], capture_output=True, text=True, timeout=15)
            reader = csv.DictReader(io.StringIO(res.stdout))
            t_ui = themed_table(border_style=col)
            t_ui.add_column("Tâche",               style="bold white", width=34)
            t_ui.add_column("Statut",              width=12)
            t_ui.add_column("Prochaine exécution", style="dim", width=20)
            count = 0
            for row in reader:
                name = (row.get("TaskName") or "").strip()
                if not name: continue
                status   = (row.get("Status") or "?").strip()
                next_run = (row.get("Next Run Time") or "?").strip()
                s_col = "green" if status.lower() == "ready" else "cyan" if status.lower() == "running" else "dim"
                t_ui.add_row(name[-34:], f"[{s_col}]{status}[/{s_col}]", next_run[:20])
                count += 1
            if count == 0:
                t_ui.add_row("—", "[dim]Aucune tâche trouvée[/dim]", "—")
            console.print(t_ui)
            info(f"{count} tâche(s) planifiée(s) trouvée(s).")
        except Exception as e: error(str(e))
    else:
        try:
            res = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
            console.print(f"[{col}]Crontab Utilisateur :[/{col}]\n{res.stdout}")
        except Exception: pass

def subnet_calc():
    col = th()["primary"]
    cidr = console.input(f"[{col}]  Réseau (ex: 192.168.1.0/24) ❯ [/{col}]").strip()
    try:
        net = ipaddress.ip_network(cidr, strict=False)
        t_ui = themed_table(border_style=col)
        t_ui.add_column("Propriété", style=col)
        t_ui.add_column("Valeur", style="white")
        t_ui.add_row("Réseau", str(net.network_address))
        t_ui.add_row("Masque", str(net.netmask))
        t_ui.add_row("Wildcard", str(net.hostmask))
        t_ui.add_row("Broadcast", str(net.broadcast_address))
        t_ui.add_row("Hôtes max", str(net.num_addresses - 2))
        t_ui.add_row("Plage IP", f"{net.network_address + 1} - {net.broadcast_address - 1}")
        console.print(t_ui)
    except Exception as e:
        error(f"Erreur de format : {e}")

def mac_lookup():
    col = th()["primary"]
    mac = console.input(f"[{col}]  Adresse MAC ❯ [/{col}]").strip()
    try:
        safe_mac = urllib.parse.quote(mac, safe=":")
        req = urllib.request.Request(f"https://api.macvendors.com/{safe_mac}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            vendor = resp.read().decode()
        success(f"Vendeur : [bold white]{vendor}[/bold white]")
    except urllib.error.HTTPError:
        error("Vendeur introuvable ou requête trop fréquente (API rate limit).")
    except Exception as e:
        error(f"Erreur réseau : {e}")

def rename_tool():
    global DISPLAY_NAME
    col = th()["primary"]
    console.print(f"[{col}]  Pseudo actuel : [bold white]{DISPLAY_NAME}[/bold white][/{col}]")
    new_name = console.input(
        f"[{col}]  Nouveau pseudo [dim](lettres/chiffres/espaces, sans accents, vide = annuler)[/dim] ❯ [/{col}]"
    ).strip()

    if not new_name:
        info("Annulé, aucun changement.")
        return

    cleaned = "".join(c for c in new_name if c.isascii() and (c.isalnum() or c in " -_")).strip()
    cleaned = cleaned[:24]
    if not cleaned:
        error("Nom invalide — utilisez des lettres/chiffres, sans accents ni symboles.")
        return

    DISPLAY_NAME = cleaned
    if _save_display_name(cleaned):
        success(f"Pseudo changé en [bold]{cleaned}[/bold] — sauvegardé, repris au prochain lancement.")
    else:
        warn(f"Pseudo changé en [bold]{cleaned}[/bold] pour cette session seulement (sauvegarde impossible).")

# ═══════════════════════════════════════════════════════
def _json_list(data):
    if data is None:
        return []
    return data if isinstance(data, list) else [data]

def _format_disk_size(value):
    try:
        size = float(value or 0)
    except (TypeError, ValueError):
        return "?"
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if size < 1024 or unit == "PB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return "?"

def _run_powershell_json(script):
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True, text=True, errors="replace", timeout=25
    )
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "PowerShell a echoue.").strip())
    output = (result.stdout or "").strip()
    if not output:
        return []
    return json.loads(output)

def _normalize_disk_row(row):
    def as_bool(value):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() == "true"

    try:
        number = int(row.get("Number"))
    except (TypeError, ValueError):
        return None

    letters = row.get("DriveLetters") or ""
    if isinstance(letters, list):
        letters = ", ".join(str(v) for v in letters if str(v).strip())
    letters = str(letters).strip() or "-"

    return {
        "number": number,
        "name": str(row.get("FriendlyName") or row.get("Model") or "Inconnu").strip(),
        "size": int(row.get("Size") or 0),
        "bus": str(row.get("BusType") or row.get("InterfaceType") or "?").strip(),
        "media": str(row.get("MediaType") or "?").strip(),
        "style": str(row.get("PartitionStyle") or "?").strip(),
        "status": str(row.get("OperationalStatus") or row.get("Status") or "?").strip(),
        "letters": letters,
        "is_boot": as_bool(row.get("IsBoot")),
        "is_system": as_bool(row.get("IsSystem")),
        "is_offline": as_bool(row.get("IsOffline")),
        "is_readonly": as_bool(row.get("IsReadOnly")),
    }

def _get_windows_disks():
    get_disk_script = r"""
$ErrorActionPreference = 'Stop'
$partitionGroups = @(Get-Partition | Where-Object { $_.DriveLetter } | Group-Object DiskNumber)
$rows = @()
foreach ($disk in Get-Disk | Sort-Object Number) {
    $letters = @()
    foreach ($group in $partitionGroups) {
        if ([int]$group.Name -eq [int]$disk.Number) {
            foreach ($part in $group.Group) {
                if ($part.DriveLetter) { $letters += "$($part.DriveLetter):" }
            }
        }
    }
    $rows += [PSCustomObject]@{
        Number = [int]$disk.Number
        FriendlyName = [string]$disk.FriendlyName
        Size = [Int64]$disk.Size
        BusType = [string]$disk.BusType
        MediaType = [string]$disk.MediaType
        PartitionStyle = [string]$disk.PartitionStyle
        OperationalStatus = (($disk.OperationalStatus | ForEach-Object { [string]$_ }) -join ', ')
        IsBoot = [bool]$disk.IsBoot
        IsSystem = [bool]$disk.IsSystem
        IsOffline = [bool]$disk.IsOffline
        IsReadOnly = [bool]$disk.IsReadOnly
        DriveLetters = ($letters -join ', ')
    }
}
$rows | ConvertTo-Json -Depth 4
""".strip()

    cim_fallback_script = r"""
$ErrorActionPreference = 'Stop'
$rows = @()
foreach ($disk in Get-CimInstance Win32_DiskDrive | Sort-Object Index) {
    $letters = @()
    foreach ($partition in Get-CimAssociatedInstance -InputObject $disk -Association Win32_DiskDriveToDiskPartition) {
        foreach ($logical in Get-CimAssociatedInstance -InputObject $partition -Association Win32_LogicalDiskToPartition) {
            if ($logical.DeviceID) { $letters += [string]$logical.DeviceID }
        }
    }
    $rows += [PSCustomObject]@{
        Number = [int]$disk.Index
        FriendlyName = [string]$disk.Model
        Size = [Int64]$disk.Size
        BusType = [string]$disk.InterfaceType
        MediaType = [string]$disk.MediaType
        PartitionStyle = '?'
        OperationalStatus = [string]$disk.Status
        IsBoot = $false
        IsSystem = $false
        IsOffline = $false
        IsReadOnly = $false
        DriveLetters = ($letters -join ', ')
    }
}
$rows | ConvertTo-Json -Depth 4
""".strip()

    errors = []
    for script in (get_disk_script, cim_fallback_script):
        try:
            disks = []
            for row in _json_list(_run_powershell_json(script)):
                disk = _normalize_disk_row(row)
                if disk:
                    disks.append(disk)
            if disks:
                return disks
        except Exception as exc:
            errors.append(str(exc))
    raise RuntimeError("Impossible de lister les disques : " + " | ".join(errors))

def _show_disk_table(disks, color):
    table = themed_table(border_style=color)
    table.add_column("Disque", style=f"bold {color}", width=10)
    table.add_column("Nom / Modèle", style="white", width=30)
    table.add_column("Taille", style="white", width=12)
    table.add_column("Lettre(s)", style="bold white", width=12)
    table.add_column("Type", style="dim", width=12)
    table.add_column("Etat", style="dim", width=16)
    table.add_column("Alertes", width=18)

    for disk in disks:
        alerts = []
        if disk["is_boot"]:
            alerts.append("[red]BOOT[/red]")
        if disk["is_system"]:
            alerts.append("[red]SYSTEME[/red]")
        if disk["is_offline"]:
            alerts.append("[yellow]OFFLINE[/yellow]")
        if disk["is_readonly"]:
            alerts.append("[yellow]READONLY[/yellow]")
        table.add_row(
            f"Disque {disk['number']}",
            disk["name"][:30],
            _format_disk_size(disk["size"]),
            disk["letters"],
            f"{disk['bus']} / {disk['media']}"[:12],
            disk["status"][:16],
            ", ".join(alerts) if alerts else "[green]OK[/green]",
        )
    console.print(table)

def _diskpart_output_has_error(output):
    lower = (output or "").lower()
    markers = (
        "error", "erreur", "failed", "echec", "échec", "invalid", "incorrect",
        "access is denied", "acces refuse", "accès refusé", "virtual disk service error",
        "service de disque virtuel", "no disk", "aucun disque"
    )
    return any(marker in lower for marker in markers)

def _run_diskpart_script(commands, mode_label):
    import threading
    from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

    fd, script_path = tempfile.mkstemp(prefix="weak_tool_diskpart_", suffix=".txt")
    output_chunks = []
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as script_file:
            script_file.write("\n".join(commands) + "\n")

        process = subprocess.Popen(
            ["diskpart", "/s", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
        )

        def collect_output():
            if process.stdout:
                for line in process.stdout:
                    output_chunks.append(line)

        reader = threading.Thread(target=collect_output, daemon=True)
        reader.start()

        with Progress(
            SpinnerColumn(style=th()["primary"]),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress:
            progress.add_task(f"Diskpart en cours - {mode_label}", total=None)
            while process.poll() is None:
                time.sleep(0.5)

        reader.join(timeout=2)
        return process.returncode, "".join(output_chunks)
    finally:
        try:
            os.remove(script_path)
        except OSError:
            pass

def diskpart_simplifie():
    col = th()["primary"]
    if platform.system().lower() != "windows":
        error("Ce module utilise Diskpart et fonctionne uniquement sous Windows.")
        return
    if not is_admin():
        error("Lancez ce multitool en administrateur avant d'utiliser Diskpart.")
        return

    warn("Module destructif : le disque choisi sera effacé entièrement.")
    try:
        disks = _get_windows_disks()
    except Exception as exc:
        error(str(exc))
        return

    if not disks:
        error("Aucun périphérique de stockage détecté.")
        return

    _show_disk_table(disks, col)
    disk_by_number = {str(disk["number"]): disk for disk in disks}
    choice = console.input(f"\n[{col}]  Numéro du disque à effacer [dim](vide = annuler)[/dim] ❯ [/{col}]").strip()
    if not choice:
        info("Opération annulée.")
        return
    if choice not in disk_by_number:
        error("Numéro de disque invalide.")
        return

    disk = disk_by_number[choice]
    console.print()
    console.print(f"[{col}]  [1][/{col}] Rapide  [dim]- diskpart clean[/dim]")
    console.print(f"[{th()['danger']}]  [2][/{th()['danger']}] Tueur   [dim]- diskpart clean all, overwrite complet[/dim]")
    mode = console.input(f"\n[{col}]  Mode de nettoyage ❯ [/{col}]").strip()
    if mode not in ("1", "2"):
        error("Mode invalide.")
        return

    console.print()
    console.print(f"[{col}]  [1][/{col}] NTFS  [dim](recommandé Windows)[/dim]")
    console.print(f"[{col}]  [2][/{col}] exFAT [dim](compatible Windows/macOS)[/dim]")
    fs_choice = console.input(f"\n[{col}]  Format final [dim](default: 1)[/dim] ❯ [/{col}]").strip() or "1"
    if fs_choice not in ("1", "2"):
        error("Format invalide.")
        return
    fs = "exfat" if fs_choice == "2" else "ntfs"

    mode_label = "Tueur / clean all" if mode == "2" else "Rapide / clean"
    clean_command = "clean all" if mode == "2" else "clean"
    commands = [
        f"select disk {disk['number']}",
        clean_command,
        "create partition primary",
        f"format fs={fs} quick",
        "assign",
        "active",
        "exit",
    ]

    warn(f"Vous allez effacer le Disque {disk['number']} : {disk['name']} ({_format_disk_size(disk['size'])}).")
    if disk["letters"] != "-":
        warn(f"Lettre(s) actuellement associée(s) : {disk['letters']}")
    if disk["is_boot"] or disk["is_system"]:
        warn("Ce disque est marqué BOOT/SYSTEME. Vérifiez deux fois avant de continuer.")

    confirmation = console.input(
        f"\n[{th()['danger']}]  Tapez OUI pour confirmer l'effacement du Disque {disk['number']} ❯ [/{th()['danger']}]"
    ).strip()
    if confirmation != "OUI":
        info("Opération annulée.")
        return

    if disk["is_boot"] or disk["is_system"]:
        second_confirmation = console.input(
            f"[{th()['danger']}]  Sécurité système : tapez SYSTEME pour continuer ❯ [/{th()['danger']}]"
        ).strip()
        if second_confirmation != "SYSTEME":
            info("Opération annulée.")
            return

    info("Diskpart va nettoyer, recréer la partition principale, formater, assigner une lettre et activer la partition.")
    try:
        returncode, output = _run_diskpart_script(commands, mode_label)
    except FileNotFoundError:
        error("diskpart.exe est introuvable sur ce système.")
        return
    except Exception as exc:
        error(f"Erreur Diskpart : {exc}")
        return

    output = (output or "").strip()
    if returncode != 0 or _diskpart_output_has_error(output):
        error("Diskpart a signalé une erreur. Vérifiez le journal ci-dessous avant de réessayer.")
        if output:
            console.print(Panel(output[-2500:], title="Journal Diskpart", border_style=th()["danger"], box=th()["box"]))
        return

    success("Opération terminée avec succès !")
    info("Appuyez sur Entrée pour revenir au menu principal.")

# ═══════════════════════════════════════════════════════
#  OUTILS TEXTE
# ═══════════════════════════════════════════════════════

def text_tools():
    col = th()["cat_uti"]
    console.print(f"\n  [{col}]Outils texte disponibles :[/{col}]")
    console.print(f"  [dim]1[/dim] Majuscules   [dim]2[/dim] Minuscules   [dim]3[/dim] Inverser   [dim]4[/dim] Slugify")
    console.print(f"  [dim]5[/dim] ROT13        [dim]6[/dim] Compteur      [dim]7[/dim] UUID       [dim]8[/dim] Capitalize")
    op = console.input(f"\n[{col}]  Choix ❯ [/{col}]").strip()
    text = console.input(f"[{col}]  Texte ❯ [/{col}]")
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Action", style=col, width=14)
    t_ui.add_column("Résultat", style="white", width=60)

    import codecs as codecs_lib
    try:
        if op == "1":
            t_ui.add_row("Majuscules", text.upper())
        elif op == "2":
            t_ui.add_row("Minuscules", text.lower())
        elif op == "3":
            t_ui.add_row("Inversé", text[::-1])
        elif op == "4":
            slug = re.sub(r'[^\w\s-]', '', text.lower())
            slug = re.sub(r'[-\s]+', '-', slug).strip('-')
            t_ui.add_row("Slug", slug)
        elif op == "5":
            t_ui.add_row("ROT13", codecs_lib.encode(text, 'rot_13'))
        elif op == "6":
            lines = text.count('\n') + (0 if text.endswith('\n') or not text else 1)
            words = len(text.split()) if text.strip() else 0
            chars = len(text)
            t_ui.add_row("Lignes", str(lines))
            t_ui.add_row("Mots", str(words))
            t_ui.add_row("Caractères", str(chars))
        elif op == "7":
            t_ui.add_row("UUID", str(uuid.uuid4()))
        elif op == "8":
            t_ui.add_row("Capitalize", text.capitalize())
        else:
            error("Choix invalide.")
    except Exception as e:
        t_ui.add_row("[red]Erreur[/red]", str(e))
    console.print(t_ui)

# ═══════════════════════════════════════════════════════
#  DATE & HEURE
# ═══════════════════════════════════════════════════════

def timestamp_converter():
    col = th()["primary"]
    console.print(f"\n  [{col}]Opérations :[/{col}]")
    console.print(f"  [dim]1[/dim] Timestamp actuel   [dim]2[/dim] Timestamp → Date   [dim]3[/dim] Différence entre dates")
    op = console.input(f"\n[{col}]  Choix ❯ [/{col}]").strip()

    if op == "1":
        now = datetime.now()
        t_ui = themed_table(border_style=col)
        t_ui.add_column("Format", style=col, width=18)
        t_ui.add_column("Valeur", style="white", width=50)
        t_ui.add_row("ISO 8601", now.isoformat())
        t_ui.add_row("Unix (s)", str(int(now.timestamp())))
        t_ui.add_row("Formaté", now.strftime("%Y-%m-%d %H:%M:%S"))
        t_ui.add_row("Date", now.strftime("%d/%m/%Y"))
        console.print(t_ui)

    elif op == "2":
        raw = console.input(f"[{col}]  Timestamp (secondes ou ms) ❯ [/{col}]").strip()
        try:
            ts = float(raw)
            if ts > 1e12: ts /= 1000
            dt = datetime.fromtimestamp(ts)
            success(f"Date : [bold white]{dt.isoformat()}[/bold white]")
        except Exception:
            error("Timestamp invalide.")

    elif op == "3":
        fmt = "%Y-%m-%d %H:%M:%S"
        d1 = console.input(f"[{col}]  Date 1 [dim](ex: 2026-01-01 12:00:00)[/dim] ❯ [/{col}]").strip()
        d2 = console.input(f"[{col}]  Date 2 ❯ [/{col}]").strip()
        try:
            dt1 = datetime.strptime(d1, fmt)
            dt2 = datetime.strptime(d2, fmt)
            diff = abs((dt2 - dt1).total_seconds())
            days = int(diff // 86400)
            hours = int((diff % 86400) // 3600)
            mins = int((diff % 3600) // 60)
            secs = int(diff % 60)
            success(f"Différence : [bold]{days}j {hours}h {mins}m {secs}s[/bold]")
        except Exception:
            error("Format invalide. Utilisez: YYYY-MM-DD HH:MM:SS")
    else:
        error("Choix invalide.")

# ═══════════════════════════════════════════════════════
#  OUTILS COULEUR
# ═══════════════════════════════════════════════════════

def color_tools():
    col = th()["primary"]
    console.print(f"\n  [{col}]Outils couleur :[/{col}]")
    console.print(f"  [dim]1[/dim] Hex → RGB   [dim]2[/dim] RGB → Hex   [dim]3[/dim] Palette")
    op = console.input(f"\n[{col}]  Choix ❯ [/{col}]").strip()

    if op == "1":
        h = console.input(f"[{col}]  Hex [dim](ex: ff5733 ou #ff5733)[/dim] ❯ [/{col}]").strip().lstrip('#')
        try:
            r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
            t_ui = themed_table(border_style=col)
            t_ui.add_column("Format", style=col, width=14)
            t_ui.add_column("Valeur", style="white", width=30)
            t_ui.add_row("RGB", f"rgb({r}, {g}, {b})")
            t_ui.add_row("RGB %", f"rgb({r*100//255}%, {g*100//255}%, {b*100//255}%)")
            console.print(t_ui)
        except Exception:
            error("Hex invalide.")

    elif op == "2":
        raw = console.input(f"[{col}]  RGB [dim](ex: 255,87,51 ou rgb(255,87,51))[/dim] ❯ [/{col}]").strip()
        m = re.match(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', raw)
        if not m: m = re.match(r'(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', raw)
        if m:
            r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
            success(f"Hex : [bold white]#{r:02x}{g:02x}{b:02x}[/bold white]")
        else:
            error("Format RGB invalide.")

    elif op == "3":
        console.print()
        for i in range(16):
            r = int(255 * (i / 15))
            g = int(255 * (1 - abs(i - 7.5) / 7.5))
            b = int(255 * (1 - i / 15))
            hex_color = '#{:02x}{:02x}{:02x}'.format(r, g, b)
            console.print(f"  [dim]{i:2d}[/dim]  [white]{hex_color}[/white]  [on rgb({r},{g},{b})]    [/on rgb({r},{g},{b})]  rgb({r},{g},{b})")
        console.print()
    else:
        error("Choix invalide.")

# ═══════════════════════════════════════════════════════
#  ENCODEURS
# ═══════════════════════════════════════════════════════

def url_html_tools():
    col = th()["cat_uti"]
    console.print(f"\n  [{col}]Encodeurs :[/{col}]")
    console.print(f"  [dim]1[/dim] URL Encode   [dim]2[/dim] URL Decode   [dim]3[/dim] HTML Entities")
    console.print(f"  [dim]4[/dim] Morse Encode [dim]5[/dim] Morse Decode")
    op = console.input(f"\n[{col}]  Choix ❯ [/{col}]").strip()
    text = console.input(f"[{col}]  Texte ❯ [/{col}]")
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Action", style=col, width=14)
    t_ui.add_column("Résultat", style="white", width=60)

    try:
        if op == "1":
            t_ui.add_row("URL Encodé", urllib.parse.quote(text))
        elif op == "2":
            t_ui.add_row("URL Décodé", urllib.parse.unquote(text))
        elif op == "3":
            encoded = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
            decoded = text.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&amp;', '&')
            t_ui.add_row("HTML Encoded", encoded)
            t_ui.add_row("HTML Decoded", decoded)
        elif op == "4":
            MORSE = {'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....','I':'..','J':'.---','K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-','U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..','0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....','6':'-....','7':'--...','8':'---..','9':'----.'}
            result = ' '.join(MORSE.get(c.upper(), c) for c in text if c != ' ')
            t_ui.add_row("Morse", result)
        elif op == "5":
            MORSE_REV = {v:k for k,v in {'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....','I':'..','J':'.---','K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-','U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..','0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....','6':'-....','7':'--...','8':'---..','9':'----.'}.items()}
            result = ''.join(MORSE_REV.get(code, '?') for code in text.split())
            t_ui.add_row("Texte", result)
        else:
            error("Choix invalide.")
    except Exception as e:
        t_ui.add_row("[red]Erreur[/red]", str(e))
    console.print(t_ui)

# ═══════════════════════════════════════════════════════
#  GÉNÉRATEUR ALÉATOIRE
# ═══════════════════════════════════════════════════════

def random_generator():
    col = th()["cat_uti"]
    console.print(f"\n  [{col}]Générateurs :[/{col}]")
    console.print(f"  [dim]1[/dim] UUID v4      [dim]2[/dim] Chaîne aléatoire   [dim]3[/dim] Hex aléatoire")
    console.print(f"  [dim]4[/dim] IP aléatoire [dim]5[/dim] MAC aléatoire")
    op = console.input(f"\n[{col}]  Choix ❯ [/{col}]").strip()
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Type", style=col, width=16)
    t_ui.add_column("Valeur", style="bold white", width=54)

    try:
        if op == "1":
            for _ in range(3):
                t_ui.add_row("UUID v4", str(uuid.uuid4()))
        elif op == "2":
            length = int(console.input(f"[{col}]  Longueur [dim](default 16)[/dim] ❯ [/{col}]") or "16")
            t_ui.add_row("Lettres+Chiffres", ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length)))
            t_ui.add_row("Lettres+Speciaux", ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(length)))
        elif op == "3":
            length = int(console.input(f"[{col}]  Longueur [dim](default 16)[/dim] ❯ [/{col}]") or "16")
            t_ui.add_row("Hex", ''.join(random.choice('0123456789abcdef') for _ in range(length)))
        elif op == "4":
            for _ in range(3):
                octets = [str(random.randint(0, 255)) for _ in range(4)]
                t_ui.add_row("IPv4", '.'.join(octets))
        elif op == "5":
            for _ in range(3):
                mac = ':'.join(['{:02x}'.format(random.randint(0, 255)) for _ in range(6)])
                t_ui.add_row("MAC", mac)
        else:
            error("Choix invalide.")
    except Exception as e:
        t_ui.add_row("[red]Erreur[/red]", str(e))
    console.print(t_ui)

# ═══════════════════════════════════════════════════════
#  COMPARATEUR
# ═══════════════════════════════════════════════════════

def diff_checker():
    col = th()["primary"]
    console.print(f"\n  [{col}]Comparateur de textes :[/{col}]")
    text1 = console.input(f"[{col}]  Texte 1 ❯ [/{col}]")
    text2 = console.input(f"[{col}]  Texte 2 ❯ [/{col}]")
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    max_lines = max(len(lines1), len(lines2))
    t_ui = themed_table(border_style=col)
    t_ui.add_column("#", style="dim", width=4)
    t_ui.add_column("Texte 1", style="white", width=30)
    t_ui.add_column("Texte 2", style="white", width=30)
    t_ui.add_column("Statut", width=10)

    for i in range(max_lines):
        l1 = lines1[i] if i < len(lines1) else ""
        l2 = lines2[i] if i < len(lines2) else ""
        if l1 == l2:
            status = "[green]=[/green]"
            c1, c2 = "white", "white"
        else:
            status = "[red]≠[/red]"
            c1, c2 = "red", "red"
        t_ui.add_row(str(i+1), f"[{c1}]{l1[:28]}[/{c1}]", f"[{c2}]{l2[:28]}[/{c2}]", status)
    console.print(t_ui)

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
    # Modules additionnels
    "29": firewall_rules,
    "30": ssh_audit,
    "31": watcher_logs,
    "32": services_manager,
    "33": env_inspector,
    "34": arp_table,
    "35": net_connections,
    "36": file_hasher,
    "37": cron_inspector,
    "38": subnet_calc,
    "39": mac_lookup,
    "40": rename_tool,
    "41": diskpart_simplifie,
    "42": text_tools,
    "43": timestamp_converter,
    "44": color_tools,
    "45": url_html_tools,
    "46": random_generator,
    "47": diff_checker,
}

# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════
def main():
    while True:
        choice = draw_menu()

        if choice in ("00","0","quit","q","exit"):
            clr()
            bye_color = th()["primary"]
            bye_msg = t("bye")
            console.print(f"\n{Align.center(f'[bold {bye_color}]{bye_msg}[/bold {bye_color}]')}\n")
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
    try:
        check_for_updates()
        main()
    except KeyboardInterrupt: clr(); sys.exit(0)
