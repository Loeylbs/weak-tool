#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import ast
import socket
import platform
import time
import hashlib
import base64
import random
import re
import uuid
import secrets
import string
import getpass
import shutil
import stat
import subprocess
import argparse
import traceback
import urllib.request
import urllib.parse
import urllib.error
import json
import csv
import io
import concurrent.futures
import ipaddress
import tempfile
import zlib
from datetime import datetime, timedelta
from urllib.error import URLError, HTTPError
from collections import deque

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ── AUTO-INSTALL ──────────────────────────────────────────
def _ensure(*pkgs):
    missing = []
    for p in pkgs:
        try:
            __import__(p)
        except ImportError:
            print(f"  [*] Installation de {p}...")
            res = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", p],
                capture_output=True, text=True,
            )
            if res.returncode != 0:
                missing.append((p, (res.stderr or res.stdout or "").strip()[-300:]))
    if missing:
        print("\n  [!] Dependances non installees :")
        for p, err in missing:
            print(f"      - {p}")
            if err:
                print(f"        {err}")
        print(f"\n  Installe-les manuellement :\n"
              f"      {sys.executable} -m pip install " + " ".join(p for p, _ in missing) + "\n")
        sys.exit(1)

_ensure("rich", "psutil", "pyfiglet", "qrcode")

from rich.console import Console, Group
from rich.panel   import Panel
from rich.table   import Table
from rich.text    import Text
from rich.rule    import Rule
from rich.align   import Align
from rich.color   import Color as RichColor
from rich.live    import Live
from rich         import box
from rich.markup  import escape as _rich_escape
import psutil
import pyfiglet
import qrcode

console = Console()

# ═══════════════════════════════════════════════════════
#  NOYAU SECURITE  (helpers partages)
# ═══════════════════════════════════════════════════════

MAX_DOWNLOAD_BYTES = 32 * 1024 * 1024   # plafond dur sur toute reponse HTTP lue
DEBUG = os.environ.get("WEAK_TOOL_DEBUG") == "1"

# ── Symboles ─────────────────────────────────────────────
# Les emoji hors du plan multilingue de base (U+FFFF et au-dela) n'ont pas de
# glyphe dans les polices par defaut de la console Windows classique : ils y
# apparaissent en carres vides. Chacun a donc un equivalent qui, lui, s'affiche
# partout. Le repli est automatique sur console Windows en mode restreint,
# et forcable avec --ascii ou WEAK_TOOL_ASCII=1.
ASCII_MODE = os.environ.get("WEAK_TOOL_ASCII") == "1"

SYMBOLS = {
    "lock":   ("🔒", "[!]"),
    "rocket": ("🚀", ">>>"),
    "live":   ("🟢", "*"),
}


def sym(name: str) -> str:
    fancy, plain = SYMBOLS.get(name, ("", ""))
    if ASCII_MODE or getattr(console, "legacy_windows", False):
        return plain
    return fancy


def esc(value) -> str:
    return _rich_escape(str(value))


def raw_print(value=""):
    console.print(str(value), markup=False, highlight=False)


# ── Validation d'hote ────────────────────────────────────
_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)"
    r"(?:\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$"
)


def valid_host(host: str) -> bool:
    if not host or len(host) > 253 or host.startswith("-"):
        return False
    if any(c.isspace() for c in host):
        return False
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass
    return bool(_HOSTNAME_RE.match(host))


def ask_host(col, label="Host", default=None):
    suffix = f" [dim](default: {default})[/dim]" if default else ""
    raw = console.input(f"[{col}]  {label}{suffix} ❯ [/{col}]").strip()
    host = raw or (default or "")
    if not host:
        return None
    if not valid_host(host):
        error(f"Hote invalide : {esc(host)}")
        return None
    return host


def ask_int(col, label, default, minimum, maximum):
    raw = console.input(f"[{col}]  {label} [dim](default: {default})[/dim] ❯ [/{col}]").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        warn(f"Valeur non numerique, {default} utilise.")
        return default
    if value < minimum or value > maximum:
        warn(f"Hors bornes [{minimum}-{maximum}], {default} utilise.")
        return default
    return value


# ── Execution de commandes ───────────────────────────────
def safe_run(cmd, timeout=10, capture=True, check_args=True):
    if isinstance(cmd, str):
        raise ValueError("safe_run exige une liste d'arguments, pas une chaine.")
    cmd = [str(c) for c in cmd]
    if check_args and any(c.startswith("-") and " " in c for c in cmd):
        raise ValueError("Argument suspect.")
    kwargs = {"timeout": timeout}
    if capture:
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      text=True, errors="replace")
    return subprocess.run(cmd, **kwargs)


# ── Fichiers de configuration ────────────────────────────
def write_private_json(path, data):
    tmp = f"{path}.tmp"
    try:
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
        return True
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False


# ── Reseau ───────────────────────────────────────────────
def read_capped(resp, limit=MAX_DOWNLOAD_BYTES):
    buf = bytearray()
    while True:
        chunk = resp.read(65536)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > limit:
            raise ValueError(f"Reponse trop volumineuse (> {limit // 1048576} Mo).")
    return bytes(buf)


def https_get_json(url, timeout=5, headers=None):
    if not url.lower().startswith("https://"):
        raise ValueError("Seul HTTPS est autorise.")
    req = urllib.request.Request(url, headers=headers or {"User-Agent": f"{TOOL_NAME}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if not resp.geturl().lower().startswith("https://"):
            raise ValueError("Redirection vers un schema non securise refusee.")
        return json.loads(read_capped(resp, 4 * 1024 * 1024).decode("utf-8", "replace"))


# ── Fichiers ─────────────────────────────────────────────
def tail_lines(path, n, chunk_size=8192):
    n = max(1, n)
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        end = f.tell()
        data = b""
        while end > 0 and data.count(b"\n") <= n:
            step = min(chunk_size, end)
            end -= step
            f.seek(end)
            data = f.read(step) + data
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return [l.decode("utf-8", "replace") for l in lines[-n:]]


def inside(child, parent):
    try:
        child = os.path.realpath(child)
        parent = os.path.realpath(parent)
        return os.path.commonpath([child, parent]) == parent
    except (ValueError, OSError):
        return False

# ── CONFIG ───────────────────────────────────────────────
TOOL_NAME    = "weak-tool"
VERSION      = "v1.7.0"
LANG         = "fr"
CMD_HISTORY  = deque(maxlen=20)

# ── ANIMATION DU MENU ────────────────────────────────────
# "soft" : la bordure reste dessinee en permanence, seule une petite trainee
#          la parcourt en surbrillance. C'est le defaut.
# "off"  : bordures totalement statiques, le menu ne se redessine plus qu'a la
#          frappe (zero scintillement sur les consoles lentes).
# "auto" : anime seulement dans un terminal capable de composer l'image entiere
#          avant de l'afficher. C'est le defaut.
# "soft" : force l'animation partout, y compris la ou elle scintille.
# "off"  : jamais d'animation.
MENU_ANIM_MODES = ("auto", "soft", "off")
MENU_ANIM       = "auto"
MENU_ANIM_DELAY = 0.22      # ~4,5 images/s : la trainee avance par pas plus
MENU_ANIM_STEP  = 4         # larges, pour la meme vitesse a l'ecran
MENU_ANIM_FPS   = 12
MENU_ANIM_COLORS = [
    "bright_magenta", "magenta", "bright_cyan", "cyan",
    "bright_yellow", "yellow", "bright_green", "green",
    "bright_blue", "blue", "bright_red", "red",
]

# ── AUTO-UPDATE (GitHub Releases) ─────────────────────────
GITHUB_REPO          = "Loeylbs/weak-tool"
UPDATE_CHECK_TIMEOUT = 5
UPDATE_DL_TIMEOUT    = 20
UPDATE_MAX_BYTES     = 8 * 1024 * 1024
UPDATE_ENABLED       = True          # desactivable via --no-update
# Seuls ces hotes peuvent servir une mise a jour. Toute autre URL presente
# dans la reponse de l'API (compromise, MITM, redirection) est refusee.
UPDATE_ALLOWED_HOSTS = {
    "github.com",
    "api.github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
}
UPDATE_CONFIG_PATH   = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), f".{TOOL_NAME}_update.json"
)
NAME_CONFIG_PATH     = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), f".{TOOL_NAME}_name.json"
)
PREFS_PATH           = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), f".{TOOL_NAME}_prefs.json"
)
FAVORITES            = set()
ARCADE_BEST          = 0        # meilleur score au 2048 du mode arcade
HEADLESS             = False    # vrai sous --run : aucun module ne doit attendre
                                # une touche, sinon le processus se fige

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
    "sunset": {
        "name": "Sunset", "primary": "orange1", "secondary": "deep_pink3",
        "accent": "gold1", "danger": "red", "success": "green",
        "warning": "gold1", "dim_col": "dark_orange", "border": "orange1",
        "cat_sys": "gold1", "cat_net": "deep_pink3", "cat_mon": "hot_pink",
        "cat_uti": "salmon1", "cat_adv": "red",
        "dots": "☀ ∙ ☀ ∙ ☀ ∙ ☀ ∙ ☀ ∙ ☀ ∙ ☀ ∙ ☀ ∙ ☀ ∙ ☀ ∙ ☀ ∙ ☀ ∙ ☀",
        "box": box.ROUNDED,
    },
    "arctic": {
        "name": "Arctic", "primary": "sky_blue1", "secondary": "steel_blue1",
        "accent": "light_cyan1", "danger": "red", "success": "turquoise2",
        "warning": "gold1", "dim_col": "steel_blue1", "border": "deep_sky_blue1",
        "cat_sys": "light_cyan1", "cat_net": "sky_blue1", "cat_mon": "turquoise2",
        "cat_uti": "steel_blue1", "cat_adv": "deep_sky_blue1",
        "dots": "❄ · ❄ · ❄ · ❄ · ❄ · ❄ · ❄ · ❄ · ❄ · ❄ · ❄ · ❄ · ❄ · ❄",
        "box": box.MINIMAL_DOUBLE_HEAD,
    },
    "arcade": {
        "name": "Arcade ★", "primary": "bright_magenta", "secondary": "bright_yellow",
        "accent": "bright_cyan", "danger": "bright_red", "success": "bright_green",
        "warning": "bright_yellow", "dim_col": "purple4", "border": "bright_magenta",
        "cat_sys": "bright_yellow", "cat_net": "bright_green", "cat_mon": "bright_cyan",
        "cat_uti": "bright_magenta", "cat_adv": "bright_red",
        "dots": "◄ ► ▲ ▼ ◄ ► ▲ ▼ ◄ ► ▲ ▼ ◄ ► ▲ ▼ ◄ ► ▲ ▼ ◄ ► ▲ ▼ ◄ ►",
        "box": box.DOUBLE_EDGE,
    },
}
THEME_NAMES = list(THEMES.keys())
CURRENT_THEME_IDX = THEME_NAMES.index("blue-magic")

# Themes qui n'apparaissent qu'une fois le secret trouve.
HIDDEN_THEMES = {"arcade"}
KONAMI_UNLOCKED = False


def visible_theme_names():
    if KONAMI_UNLOCKED:
        return list(THEME_NAMES)
    return [n for n in THEME_NAMES if n not in HIDDEN_THEMES]


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
        "n48": "Espace Disque", "n49": "Gros Fichiers", "n50": "Doublons",
        "n51": "JSON / CSV / YAML", "n52": "Testeur Regex", "n53": "Explicateur Cron",
        "n54": "Exporter Résultat", "n55": "Inspecteur TLS", "n56": "En-têtes HTTP",
        "n57": "Enregistrements DNS", "n58": "Décodeur JWT", "n59": "Préférences",
        "n60": "Batterie / Alim", "n61": "Phrase de Passe", "n62": "Intégrité Fichiers",
        "n63": "Benchmark", "n64": "Ports en Écoute", "n65": "Bilan de Santé",
        "n99": "Mode Arcade",
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
        "n48": "Disk Usage", "n49": "Big Files", "n50": "Duplicates",
        "n51": "JSON / CSV / YAML", "n52": "Regex Tester", "n53": "Cron Explainer",
        "n54": "Export Result", "n55": "TLS Inspector", "n56": "HTTP Headers",
        "n57": "DNS Records", "n58": "JWT Decoder", "n59": "Preferences",
        "n60": "Battery / Power", "n61": "Passphrase", "n62": "File Integrity",
        "n63": "Benchmark", "n64": "Listening Ports", "n65": "Health Check",
        "n99": "Arcade Mode",
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
    LAST_RESULT["columns"] = []
    LAST_RESULT["rows"] = []
    return RecordingTable(*args, **kwargs)

def success(msg):
    console.print(f"  [{th()['success']}]✔ {msg}[/{th()['success']}]")

def error(msg):
    console.print(f"  [{th()['danger']}]✘ {msg}[/{th()['danger']}]")

def info(msg):
    console.print(f"  [{th()['secondary']}]ℹ {msg}[/{th()['secondary']}]")

def warn(msg):
    console.print(f"  [{th()['warning']}]⚠ {msg}[/{th()['warning']}]")

def sensitive_notice(detail: str = "") -> bool:
    col = th()["warning"]
    suffix = f" ({detail})" if detail else ""
    console.print(f"  [{col}]{sym('lock')} Info sensible{suffix}[/{col}]")
    console.print(f"  [{col}]Rien n'est encore affiché. Vérifie que personne ne regarde "
                  f"et que ton écran n'est pas partagé.[/{col}]")
    console.print()
    try:
        answer = console.input(
            f"  [{col}]↵ Entrée pour afficher · [dim]n[/dim] pour annuler ❯ [/{col}]"
        ).strip().lower()
    except (KeyboardInterrupt, EOFError):
        console.print()
        info("Affichage annulé.")
        return False
    if answer in ("n", "non", "no", "q"):
        info("Affichage annulé.")
        return False
    console.print()
    return True

def _human_duration(seconds: float) -> str:
    if seconds < 1:
        return "< 1 seconde"
    units = [
        ("siecle(s)", 100 * 365.25 * 86400),
        ("annee(s)", 365.25 * 86400),
        ("jour(s)", 86400),
        ("heure(s)", 3600),
        ("minute(s)", 60),
        ("seconde(s)", 1),
    ]
    for name, size in units:
        if seconds >= size:
            value = seconds / size
            text = f"{value:.2e}" if value > 1e6 else f"{value:,.1f}"
            return f"{text} {name}"
    return f"{seconds:.0f} seconde(s)"

# Mots de passe les plus frequents dans les fuites publiques connues
# (echantillon hors ligne, pour un controle rapide sans requete reseau).
COMMON_PASSWORDS = {
    "123456", "password", "123456789", "12345678", "12345", "111111",
    "1234567", "sunshine", "qwerty", "iloveyou", "admin", "welcome",
    "monkey", "login", "abc123", "starwars", "123123", "dragon",
    "passw0rd", "master", "hello", "freedom", "whatever", "qazwsx",
    "trustno1", "letmein", "football", "baseball", "shadow", "superman",
    "michael", "ninja", "mustang", "password1", "000000", "1234567890",
    "azerty", "motdepasse", "bonjour", "soleil", "loulou", "doudou",
    "chocolat", "marseille",
}

# ── AUTO-UPDATE ────────────────────────────────────────────
def _load_update_config():
    try:
        with open(UPDATE_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_update_config(data):
    write_private_json(UPDATE_CONFIG_PATH, data)

# ── NOM PERSONNALISÉ (pseudo) ─────────────────────────────
# Typographies proposees pour le pseudo. "blocks" est dessinee par l'outil
# lui-meme (voir BLOCK_GLYPHS) : elle ne depend d'aucune police pyfiglet et
# rend le meme resultat partout. "auto" laisse l'outil prendre la plus large
# qui tient a l'ecran.
BANNER_FONT_CHOICES = [
    "blocks", "auto", "block", "doom", "speed", "slant", "chunky",
    "cyberlarge", "standard", "shadow", "rounded", "colossal", "starwars",
    "larry3d", "banner3-D", "epic", "stop", "graffiti", "small", "mini",
]
BANNER_STYLES = ("gradient", "wave", "vertical", "solid")
DEFAULT_BANNER_FONT  = "blocks"
DEFAULT_BANNER_STYLE = "gradient"


def _load_name_config():
    try:
        with open(NAME_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_name_config():
    return write_private_json(NAME_CONFIG_PATH, {
        "display_name": DISPLAY_NAME,
        "banner_font": BANNER_FONT,
        "banner_style": BANNER_STYLE,
    })


_NAME_CFG    = _load_name_config()
DISPLAY_NAME = (str(_NAME_CFG.get("display_name") or "").strip() or TOOL_NAME)[:24]
BANNER_FONT  = _NAME_CFG.get("banner_font")
BANNER_FONT  = BANNER_FONT if BANNER_FONT in BANNER_FONT_CHOICES else DEFAULT_BANNER_FONT
BANNER_STYLE = _NAME_CFG.get("banner_style")
BANNER_STYLE = BANNER_STYLE if BANNER_STYLE in BANNER_STYLES else DEFAULT_BANNER_STYLE

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
    if not UPDATE_ENABLED or not GITHUB_REPO or "/" not in GITHUB_REPO:
        return None
    owner, _, repo = GITHUB_REPO.partition("/")
    url = (f"https://api.github.com/repos/{urllib.parse.quote(owner)}"
           f"/{urllib.parse.quote(repo)}/releases/latest")
    try:
        return https_get_json(url, timeout=UPDATE_CHECK_TIMEOUT, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{TOOL_NAME}-updater",
        })
    except (URLError, HTTPError, TimeoutError, ValueError, OSError):
        return None


def _is_trusted_update_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return False
    return (parsed.scheme.lower() == "https"
            and (parsed.hostname or "").lower() in UPDATE_ALLOWED_HOSTS)

def _pick_asset(release):
    own_name = os.path.basename(os.path.abspath(__file__))
    assets = release.get("assets") or []
    chosen = None
    for a in assets:
        if a.get("name", "").lower() == own_name.lower():
            chosen = a
            break
    if chosen is None:
        for a in assets:
            if a.get("name", "").lower().endswith(".py"):
                chosen = a
                break
    if chosen is None:
        return None
    if not _is_trusted_update_url(chosen.get("browser_download_url", "")):
        return None
    return chosen


def _pick_checksum_asset(release, asset):
    wanted = f"{asset.get('name', '')}.sha256".lower()
    for a in release.get("assets") or []:
        if a.get("name", "").lower() == wanted:
            if _is_trusted_update_url(a.get("browser_download_url", "")):
                return a
    return None


def _fetch_expected_digest(asset_ck):
    try:
        req = urllib.request.Request(
            asset_ck["browser_download_url"],
            headers={"User-Agent": f"{TOOL_NAME}-updater"},
        )
        with urllib.request.urlopen(req, timeout=UPDATE_CHECK_TIMEOUT) as resp:
            if not _is_trusted_update_url(resp.geturl()):
                return None
            raw = read_capped(resp, 4096).decode("utf-8", "replace")
    except Exception:
        return None
    token = raw.strip().split()[0].lower() if raw.strip() else ""
    return token if len(token) == 64 and all(c in "0123456789abcdef" for c in token) else None

def _download_with_progress(url, dest_path):
    from rich.progress import (Progress, BarColumn, DownloadColumn,
                                TransferSpeedColumn, TimeRemainingColumn)
    if not _is_trusted_update_url(url):
        raise ValueError("URL de mise a jour non autorisee.")

    req = urllib.request.Request(url, headers={"User-Agent": f"{TOOL_NAME}-updater"})
    digest = hashlib.sha256()
    written = 0
    with urllib.request.urlopen(req, timeout=UPDATE_DL_TIMEOUT) as resp:
        if not _is_trusted_update_url(resp.geturl()):
            raise ValueError("Redirection vers un hote non autorise.")
        total = int(resp.headers.get("Content-Length", 0) or 0)
        if total > UPDATE_MAX_BYTES:
            raise ValueError(f"Mise a jour trop volumineuse ({total} octets).")
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
                    written += len(chunk)
                    if written > UPDATE_MAX_BYTES:
                        raise ValueError("Plafond de telechargement depasse.")
                    f.write(chunk)
                    digest.update(chunk)
                    progress.update(task, advance=len(chunk))
    return digest.hexdigest()


def _looks_like_weak_tool(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
    except (OSError, UnicodeDecodeError):
        return False, "fichier illisible ou non-UTF8"
    if len(code) < 2000:
        return False, "fichier anormalement court"
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return False, f"Python invalide (ligne {exc.lineno})"
    if "def main(" not in code or "ACTIONS" not in code:
        return False, "structure inattendue (main/ACTIONS absents)"
    return True, ""

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
        title=f"[bold {th()['warning']}]{sym('rocket')} MISE A JOUR DISPONIBLE[/bold {th()['warning']}]",
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
    try:
        subprocess.Popen([sys.executable, os.path.abspath(__file__)] + sys.argv[1:])
    except Exception as e:
        error(f"Relance impossible ({esc(e)}) — relance manuellement.")
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

def _apply_update(asset, release=None):
    script_path = os.path.abspath(__file__)
    script_dir  = os.path.dirname(script_path)
    tmp_path    = os.path.join(script_dir, f".{TOOL_NAME}_new.tmp")

    def cleanup():
        try: os.remove(tmp_path)
        except OSError: pass

    try:
        info("Telechargement de la mise a jour...")
        got_digest = _download_with_progress(asset["browser_download_url"], tmp_path)
    except Exception as e:
        error(f"Echec du telechargement : {esc(e)}")
        cleanup()
        return False

    # 2. Condensat publie
    expected = None
    ck_asset = _pick_checksum_asset(release or {}, asset)
    if ck_asset:
        expected = _fetch_expected_digest(ck_asset)

    if expected:
        if not secrets.compare_digest(expected, got_digest):
            error("INTEGRITE COMPROMISE : le condensat ne correspond pas.")
            info(f"attendu  : {expected}")
            info(f"obtenu   : {got_digest}")
            warn("Mise a jour abandonnee, aucun fichier remplace.")
            cleanup()
            return False
        success("Condensat SHA-256 verifie.")
    else:
        # 3. Pas de condensat publie : on ne remplace pas en silence.
        warn("Aucun condensat SHA-256 publie pour cette release.")
        info(f"SHA-256 du fichier recu : {got_digest}")
        info("Compare-le a celui annonce sur la page de la release avant de continuer.")
        if console.input(
            f"  [{th()['danger']}]Tapez OUI pour installer malgre tout ❯ [/{th()['danger']}]"
        ).strip() != "OUI":
            info("Mise a jour annulee.")
            cleanup()
            return False

    # 4. Sanite du contenu
    ok, why = _looks_like_weak_tool(tmp_path)
    if not ok:
        error(f"Fichier rejete : {esc(why)}")
        cleanup()
        return False

    # 5. Sauvegarde obligatoire
    backup_path = script_path + ".bak"
    try:
        shutil.copy2(script_path, backup_path)
    except Exception as e:
        error(f"Sauvegarde impossible ({esc(e)}) — mise a jour annulee par securite.")
        cleanup()
        return False

    try:
        os.replace(tmp_path, script_path)
        success(f"Mise a jour installee (sauvegarde : {os.path.basename(backup_path)}). Redemarrage...")
        time.sleep(0.8)
        _relaunch()
        return True
    except PermissionError:
        warn("Fichier verrouille, finalisation via un script relais...")
        _spawn_relay_updater(tmp_path, script_path)
        sys.exit(0)
    except Exception as e:
        error(f"Echec de l'installation : {esc(e)}")
        try:
            shutil.copy2(backup_path, script_path)
            info("Version precedente restauree.")
        except Exception:
            error(f"Restauration impossible — recupere {backup_path} manuellement.")
        cleanup()
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
        _apply_update(asset, release)
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
# ── TYPOGRAPHIE DU PSEUDO ─────────────────────────────────
# Police « blocs » dessinee a la main : 5 lignes de 5 pixels par caractere.
# Elle donne le rendu plein des logos ASCII modernes sans dependre d'une
# police pyfiglet particuliere (celles a base de blocs sont absentes des
# versions courantes du paquet).
BLOCK_GLYPHS = {
    "A": ("01110", "10001", "11111", "10001", "10001"),
    "B": ("11110", "10001", "11110", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "11110", "10000", "11111"),
    "F": ("11111", "10000", "11110", "10000", "10000"),
    "G": ("01111", "10000", "10011", "10001", "01111"),
    "H": ("10001", "10001", "11111", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "11100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001"),
    "O": ("01110", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "11110", "10000", "10000"),
    "Q": ("01110", "10001", "10101", "10011", "01111"),
    "R": ("11110", "10001", "11110", "10010", "10001"),
    "S": ("01111", "10000", "01110", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10101", "11011", "10001"),
    "X": ("10001", "01010", "00100", "01010", "10001"),
    "Y": ("10001", "01010", "00100", "00100", "00100"),
    "Z": ("11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10011", "10101", "11001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00110", "01000", "11111"),
    "3": ("11110", "00001", "00110", "00001", "11110"),
    "4": ("00110", "01010", "10010", "11111", "00010"),
    "5": ("11111", "10000", "11110", "00001", "11110"),
    "6": ("01110", "10000", "11110", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000"),
    "8": ("01110", "10001", "01110", "10001", "01110"),
    "9": ("01110", "10001", "01111", "00001", "01110"),
    "-": ("00000", "00000", "11111", "00000", "00000"),
    "_": ("00000", "00000", "00000", "00000", "11111"),
    ".": ("00000", "00000", "00000", "00000", "00100"),
    " ": ("00000", "00000", "00000", "00000", "00000"),
}


def _block_font_lines(text: str, cell: str = "██", gap: int = 1):
    """Rend le texte avec la police blocs interne. `cell` est le motif d'un
    pixel allume : deux caracteres donnent des lettres bien proportionnees,
    un seul les rend deux fois plus etroites quand la place manque."""
    chars = [c for c in text.upper() if c in BLOCK_GLYPHS]
    if not chars:
        return []
    blank = " " * len(cell)
    sep = blank * gap
    lines = []
    for row in range(5):
        parts = []
        for ch in chars:
            bits = BLOCK_GLYPHS[ch][row]
            parts.append("".join(cell if b == "1" else blank for b in bits))
        lines.append(sep.join(parts))
    return lines


def _figlet_lines(text: str, font: str, width: int):
    try:
        out = pyfiglet.figlet_format(text, font=font, width=max(width, 40))
    except Exception:
        return None
    lines = out.rstrip("\n").splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return None
    # pyfiglet aligne a gauche avec un creux commun : on le retire pour que le
    # centrage porte sur le dessin lui-meme et non sur son remplissage.
    pad = min((len(l) - len(l.lstrip(" ")) for l in lines if l.strip()), default=0)
    lines = [l[pad:].rstrip() for l in lines]
    if max((len(l) for l in lines), default=0) > width:
        return None
    return lines


def _pad_block(lines):
    """Aligne toutes les lignes sur la meme largeur. Chaque ligne du logo est
    centree separement a l'affichage : sans ce calage, une ligne plus courte
    que les autres se retrouve decalee et le logo part de travers."""
    lines = [l.rstrip() for l in lines]
    span = max((len(l) for l in lines), default=0)
    return [l.ljust(span) for l in lines]


def _banner_lines(text: str, width: int):
    """Retourne les lignes du logo pour le pseudo, en respectant la typo
    choisie et en repliant sur une variante plus etroite si l'ecran est trop
    petit. Le repli garantit qu'un pseudo long reste toujours affichable."""
    return _pad_block(_banner_lines_raw(text, width))


def _banner_lines_raw(text: str, width: int):
    if BANNER_FONT == "blocks":
        for cell, gap in (("██", 1), ("█", 1), ("█", 0)):
            lines = _block_font_lines(text, cell=cell, gap=gap)
            if lines and max(len(l) for l in lines) <= width:
                return lines
    elif BANNER_FONT != "auto":
        lines = _figlet_lines(text, BANNER_FONT, width)
        if lines:
            return lines

    for cell, gap in (("██", 1), ("█", 1)):
        lines = _block_font_lines(text, cell=cell, gap=gap)
        if lines and max(len(l) for l in lines) <= width:
            return lines
    for font in ("block", "doom", "speed", "standard", "small", "mini"):
        lines = _figlet_lines(text, font, width)
        if lines:
            return lines
    return [f"/ {text.upper()} \\"]


# Degrade applique au logo, par theme. Les couleurs sont interpolees en RGB :
# le fondu est continu au lieu de sauter d'une teinte a l'autre.
THEME_BANNER_STOPS = {
    "neon":       ["bright_yellow", "bright_cyan", "bright_magenta", "bright_cyan", "bright_yellow"],
    "cyber":      ["bright_cyan", "cyan", "blue", "bright_blue", "bright_cyan"],
    "matrix":     ["bright_green", "green", "bright_green", "green", "bright_green"],
    "blood":      ["bright_red", "red", "dark_red", "red", "bright_red"],
    "graffiti":   ["bright_magenta", "bright_cyan", "bright_yellow", "bright_cyan", "bright_magenta"],
    "dracula":    ["bright_magenta", "purple4", "bright_cyan", "purple4", "bright_magenta"],
    "blue-magic": ["bright_cyan", "cyan", "blue", "bright_blue", "bright_cyan"],
    "sunset":     ["gold1", "orange1", "deep_pink3", "hot_pink", "gold1"],
    "arctic":     ["light_cyan1", "sky_blue1", "deep_sky_blue1", "steel_blue1", "light_cyan1"],
    "arcade":     ["bright_magenta", "bright_yellow", "bright_cyan", "bright_green", "bright_magenta"],
}

_RGB_CACHE = {}


def _rgb_of(color_name: str):
    if color_name not in _RGB_CACHE:
        try:
            trip = RichColor.parse(color_name).get_truecolor()
            _RGB_CACHE[color_name] = (trip.red, trip.green, trip.blue)
        except Exception:
            _RGB_CACHE[color_name] = (200, 200, 200)
    return _RGB_CACHE[color_name]


def _banner_stops():
    key = THEME_NAMES[CURRENT_THEME_IDX]
    stops = THEME_BANNER_STOPS.get(key)
    if not stops:
        stops = [th()["primary"], th()["accent"], th()["secondary"], th()["primary"]]
    return [_rgb_of(c) for c in stops]


def _color_at(stops, pos: float) -> str:
    """Couleur du degrade a la position pos (0.0 -> 1.0), en #RRGGBB."""
    pos = max(0.0, min(1.0, pos))
    if len(stops) == 1:
        r, g, b = stops[0]
        return f"#{r:02x}{g:02x}{b:02x}"
    scaled = pos * (len(stops) - 1)
    i = min(int(scaled), len(stops) - 2)
    f = scaled - i
    (r1, g1, b1), (r2, g2, b2) = stops[i], stops[i + 1]
    r = int(r1 + (r2 - r1) * f)
    g = int(g1 + (g2 - g1) * f)
    b = int(b1 + (b2 - b1) * f)
    return f"#{r:02x}{g:02x}{b:02x}"


def _banner_logo_rows(lines):
    """Peint le logo selon le style choisi et renvoie les lignes pretes a
    afficher. Le degrade est horizontal (ou diagonal en mode wave) : il suit la
    forme des lettres au lieu de colorer chaque ligne d'un bloc uni."""
    if not lines:
        return []
    stops = _banner_stops()
    span = max((len(l) for l in lines), default=1) or 1
    height = max(1, len(lines))
    rows = []

    if BANNER_STYLE == "solid":
        color = th()["primary"]
        return [Align.center(Text(line, style=f"bold {color}")) for line in lines]

    if BANNER_STYLE == "vertical":
        for row, line in enumerate(lines):
            color = _color_at(stops, row / max(1, height - 1) if height > 1 else 0.0)
            rows.append(Align.center(Text(line, style=f"bold {color}")))
        return rows

    diagonal = BANNER_STYLE == "wave"
    for row, line in enumerate(lines):
        text = Text()
        offset = (row / height) * 0.35 if diagonal else 0.0
        for col, ch in enumerate(line):
            if ch == " ":
                text.append(" ")
                continue
            pos = (col / max(1, span - 1)) + offset
            text.append(ch, style=f"bold {_color_at(stops, pos % 1.0 if diagonal else pos)}")
        rows.append(Align.center(text))
    return rows


def _gradient_banner(lines):
    for row in _banner_logo_rows(lines):
        console.print(row)

def _screen_width():
    # On ne depasse jamais la largeur reelle de la console : forcer un plancher
    # plus large qu'elle faisait passer le logo et les cadres a la ligne.
    # Le plafond laisse de la marge pour aligner les cinq categories sur une
    # rangee sur un ecran large.
    try:
        real = console.width
    except Exception:
        real = 84
    return max(40, min(real, 200))


def _logo_width():
    """Largeur utilisable par le logo, avec une marge pour le centrage."""
    return max(20, _screen_width() - 2)

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

def _starfield_rows(width, rows=2):
    rng = random.Random(1337)
    chars = (".", "·", "*")
    dim, sec = th()["dim_col"], th()["secondary"]
    out = []
    for _ in range(rows):
        line = Text()
        for _c in range(width):
            if rng.random() < 0.035:
                ch = rng.choice(chars)
                style = f"bold {sec}" if rng.random() < 0.3 else dim
                line.append(ch, style=style)
            else:
                line.append(" ")
        out.append(Align.center(line))
    return out


def _pixel_fade_rows(width, rows=2, base_density=0.14):
    rng = random.Random(2026)
    pri, dim = th()["primary"], th()["dim_col"]
    out = []
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
        out.append(Align.center(line))
    return out


def _starfield(width, rows=2):
    for row in _starfield_rows(width, rows):
        console.print(row)


def _pixel_fade(width, rows=2, base_density=0.14):
    for row in _pixel_fade_rows(width, rows, base_density):
        console.print(row)

def _anim_color():
    return th()["primary"]

def _banner_parts(width, level="full"):
    """Elements de la banniere, du plus decore au plus ras.

    `level` permet de la comprimer quand la fenetre est basse : « full » avec
    champ d'etoiles et fondu de pixels, « slim » avec le seul logo, « small »
    avec un logo de trois lignes, « mini » reduit a une ligne de texte. Sans
    cela la banniere et le menu depassent la hauteur du terminal, qui se met
    alors a defiler et a scintiller a chaque rafraichissement.
    """
    sec, dim = th()["secondary"], th()["dim_col"]
    privilege = "ADMIN" if is_admin() else "USER"
    meta = (f"{VERSION} · {privilege} · {getpass.getuser()}@{platform.node()} · "
            f"{datetime.now().strftime('%H:%M:%S')}")

    if level == "mini":
        pri = th()["primary"]
        return [Align.center(Text.assemble(
            (f"/ {DISPLAY_NAME.upper()} \\", f"bold {pri}"), ("   ", dim), (meta, dim)))]

    parts = []
    if level == "full":
        parts.append(Text(""))
        parts += _starfield_rows(width)

    if level == "small":
        # Deux lignes de moins que le logo plein, mais le pseudo reste dessine.
        # La typo choisie est conservee si elle tient deja en quatre lignes ;
        # sinon on bascule sur la plus proche qui rentre.
        lines = _banner_lines(DISPLAY_NAME, _logo_width())
        if len(lines) > 4:
            for font in ("small", "mini"):
                candidate = _figlet_lines(DISPLAY_NAME, font, _logo_width())
                if candidate and len(candidate) <= 4:
                    lines = _pad_block(candidate)
                    break
        parts += _banner_logo_rows(lines)
    else:
        parts += _banner_logo_rows(_banner_lines(DISPLAY_NAME, _logo_width()))

    if level == "full":
        parts += _pixel_fade_rows(width)
    parts.append(Align.center(Text(meta, style=dim)))
    if level == "full":
        parts.append(Align.center(Text(f"theme:{th()['name']}", style=sec)))
    parts.append(Text(""))
    return parts


def banner(level="full"):
    clr()
    for part in _banner_parts(_screen_width(), level):
        console.print(part)

# ── CATÉGORIES DU MENU ────────────────────────────────────
def get_cats():
    cats = [
        (t("c_sys"), th()["cat_sys"], [
            ("01", t("sys1")), ("02", t("sys2")), ("03", t("sys3")),
            ("04", t("sys4")), ("05", t("sys5")), ("06", t("sys6")),
            ("32", t("new4")), ("33", t("new5")), ("37", t("new9")),
            ("41", t("new13")), ("48", t("n48")), ("60", t("n60")),
            ("62", t("n62")), ("63", t("n63")),
        ]),
        (t("c_net"), th()["cat_net"], [
            ("07", t("net1")), ("08", t("net2")), ("09", t("net3")),
            ("10", t("net4")), ("11", t("net5")), ("12", t("net6")),
            ("29", t("new1")), ("30", t("new2")), ("34", t("new6")),
            ("35", t("new7")), ("38", t("new10")), ("39", t("new11")),
            ("55", t("n55")), ("56", t("n56")), ("57", t("n57")),
            ("64", t("n64")),
        ]),
        (t("c_mon"), th()["cat_mon"], [
            ("13", t("mon1")), ("14", t("mon2")), ("31", t("new3")),
            ("65", t("n65")),
        ]),
        (t("c_uti"), th()["cat_uti"], [
            ("15", t("uti1")), ("16", t("uti2")), ("17", t("uti3")),
            ("18", t("uti4")), ("19", t("uti5")), ("36", t("new8")),
            ("42", t("new14")), ("43", t("new15")), ("44", t("new16")),
            ("45", t("new17")), ("46", t("new18")), ("49", t("n49")),
            ("50", t("n50")), ("51", t("n51")), ("52", t("n52")),
            ("53", t("n53")), ("58", t("n58")), ("61", t("n61")),
        ]),
        (t("c_adv"), th()["cat_adv"], [
            ("21", t("adv1")), ("22", t("adv2")), ("23", t("adv3")),
            ("24", t("adv4")), ("25", t("adv5")), ("26", t("adv6")),
            ("40", t("new12")), ("47", t("new19")), ("54", t("n54")),
            ("28", t("hist")), ("27", t("theme")), ("20", t("lang")),
            ("59", t("n59")), ("00", t("quit")),
        ]),
    ]
    if KONAMI_UNLOCKED:
        # Module secret : n'apparait qu'une fois le code trouve.
        adv = cats[4]
        items = list(adv[2])
        items.insert(len(items) - 1, ("99", t("n99")))
        cats[4] = (adv[0], adv[1], items)
    if not FAVORITES:
        return cats
    return [(title, color, [(code, ("★ " + label) if code in FAVORITES else label)
                            for code, label in items])
            for title, color, items in cats]

def _item_matches(query: str, code: str, label: str) -> bool:
    q = query.strip().lower()
    if not q:
        return True
    lbl = label.lower()
    if q.isdigit():
        return code.startswith(q) or q in lbl
    return q in lbl or q in code.lower()


def _menu_footer_hint(cats, typed: str, dim: str) -> Text:
    if typed:
        matches = sum(1 for _, _, items in cats for code, label in items
                       if code != "00" and _item_matches(typed, code, label))
        msg = f"{matches} correspondance(s)" if matches else "aucune correspondance"
    else:
        msg = "astuce : *08 pour (dé)favoriser · nom de module pour chercher"
    return Text(msg, style=dim)


_GAUGE_CACHE = {"t": 0.0, "cpu": 0.0, "ram": 0.0}


def _live_gauge_text(dim: str) -> Text:
    now = time.monotonic()
    if now - _GAUGE_CACHE["t"] > 0.6:
        try:
            _GAUGE_CACHE["cpu"] = psutil.cpu_percent(interval=None)
            _GAUGE_CACHE["ram"] = psutil.virtual_memory().percent
        except Exception:
            pass
        _GAUGE_CACHE["t"] = now
    cpu, ram = _GAUGE_CACHE["cpu"], _GAUGE_CACHE["ram"]
    col_c = "green" if cpu < 60 else "yellow" if cpu < 85 else "red"
    col_r = "green" if ram < 60 else "yellow" if ram < 85 else "red"
    return Text.assemble(
        ("CPU ", dim), (f"{cpu:4.1f}%", f"bold {col_c}"), ("   ", dim),
        ("RAM ", dim), (f"{ram:4.1f}%", f"bold {col_r}"), ("   ", dim),
        (datetime.now().strftime("%H:%M:%S"), dim),
    )


def _favorites_bar(width: int):
    if not FAVORITES:
        return None
    acc = th()["accent"]
    t_obj = Text()
    for i, code in enumerate(sorted(FAVORITES)):
        label, color = _color_for(code)
        label = label[2:] if label.startswith("★ ") else label
        if i:
            t_obj.append("   ")
        t_obj.append(f"★{code} ", style=f"bold {acc}")
        t_obj.append(label, style=color)
    return Panel(
        t_obj,
        title=Text("★ FAVORIS", style=f"bold {acc}"),
        title_align="center",
        border_style=acc,
        box=th()["box"],
        expand=False,
        width=min(width, 140),
        padding=(0, 1),
    )


# Les boites « minimales » (matrix, arctic) n'ont ni montants ni coins : dans
# le menu il n'y a alors aucun cadre a parcourir, et la trainee lumineuse est
# invisible. Ces themes recoivent un cadre plein pour le menu uniquement, les
# tableaux gardant le style d'origine.
_MENU_BOX_FALLBACK = {
    "matrix": box.SQUARE,
    "arctic": box.DOUBLE,
}


def _menu_box():
    theme_key = THEME_NAMES[CURRENT_THEME_IDX]
    b = th()["box"]
    if b.top_left.strip() and b.mid_left.strip():
        return b
    return _MENU_BOX_FALLBACK.get(theme_key, box.SQUARE)


def _make_panel(title: str, color: str, items: list, width: int = 32, border_color: str = None, query: str = "") -> Panel:
    border_color = border_color or color
    t_obj = Text()
    max_label = max(10, width - 10)
    dim = th()["dim_col"]
    for num, label in items:
        clipped = label if len(label) <= max_label else label[:max_label - 3] + "..."
        if query and not _item_matches(query, num, label):
            t_obj.append(f"[{num}] ", style=dim)
            t_obj.append(f"{clipped}\n", style=dim)
        else:
            t_obj.append(f"[{num}] ", style=f"bold {border_color}")
            t_obj.append(f"{clipped}\n", style=color)
    t_obj.rstrip()
    return Panel(
        t_obj,
        title=Text(f"/ {title} \\", style=f"bold {border_color}"),
        title_align="center",
        border_style=border_color,
        box=_menu_box(),
        expand=False,
        width=width,
        padding=(0, 1),
    )

# ── AFFICHAGE SYNCHRONISE (anti-scintillement) ────────────
# « Synchronized output », mode prive DEC 2026 : le terminal met son affichage
# en pause entre les deux sequences et ne repeint qu'une fois l'image complete
# recue. Sans cela il repeint pendant l'ecriture et l'on voit passer des images
# a moitie tracees — c'est ce que l'oeil percoit comme un clignotement.
# Les terminaux qui ne connaissent pas ce mode ignorent la sequence.
_SYNC_BEGIN = "\x1b[?2026h"
_SYNC_END   = "\x1b[?2026l"


def _sync_supported() -> bool:
    try:
        return bool(console.is_terminal) and not getattr(console, "legacy_windows", False)
    except Exception:
        return False


def _sync_write(seq: str):
    if not _sync_supported():
        return
    try:
        console.file.write(seq)
        console.file.flush()
    except Exception:
        pass


def _synced_update(live, renderable):
    """Remplace une image par une autre sans laisser voir d'etat transitoire."""
    _sync_write(_SYNC_BEGIN)
    try:
        live.update(renderable, refresh=True)
    finally:
        _sync_write(_SYNC_END)


def _alt_screen_usable() -> bool:
    """Le buffer alternatif est-il reellement disponible ?

    Rich n'emet la sequence que si la console accepte les codes VT
    (`is_terminal and not legacy_windows`). Sur une console Windows heritee le
    reglage est ignore en silence : autant le savoir ici pour adapter le reste.
    """
    return _sync_supported()


def _legacy_console() -> bool:
    """Console Windows sans mode VT : Rich y dessine cellule par cellule via
    l'API Win32, un mode ou l'animation scintille quoi qu'on fasse."""
    try:
        return bool(getattr(console, "legacy_windows", False)) and console.is_terminal
    except Exception:
        return False


def _compositing_terminal() -> bool:
    """Le terminal compose-t-il l'image avant de l'afficher ?

    Distinction essentielle, et differente du mode VT : conhost.exe (la fenetre
    « Invite de commandes ») accepte les codes VT mais applique les octets au
    fur et a mesure qu'il les recoit, en repeignant a chaque ligne. Reecrire
    l'ecran plusieurs fois par seconde y reste visible quoi qu'on optimise.
    Windows Terminal, VS Code, ConEmu, WezTerm et les terminaux Unix peignent
    l'image d'un seul tenant et n'ont pas ce defaut.

    Aucun code VT ne permet de poser la question : on identifie le terminal par
    les variables qu'il publie dans l'environnement.
    """
    if os.name != "nt":
        return True
    env = os.environ
    return bool(
        env.get("WT_SESSION")        # Windows Terminal
        or env.get("WT_PROFILE_ID")
        or env.get("TERM_PROGRAM")   # VS Code, et la plupart des terminaux tiers
        or env.get("ConEmuPID")      # ConEmu / Cmder
        or env.get("WEZTERM_PANE")
        or env.get("ALACRITTY_WINDOW_ID")
    )


def _terminal_label() -> str:
    if os.name != "nt":
        return "terminal Unix"
    env = os.environ
    if env.get("WT_SESSION") or env.get("WT_PROFILE_ID"):
        return "Windows Terminal"
    if env.get("TERM_PROGRAM"):
        return str(env.get("TERM_PROGRAM"))
    if env.get("ConEmuPID"):
        return "ConEmu"
    if _legacy_console():
        return "console Windows (sans VT)"
    return "conhost.exe (Invite de commandes)"


def _anim_active() -> bool:
    """L'animation doit-elle tourner ?

    En mode « auto » elle ne tourne que dans un terminal qui compose l'image
    avant de l'afficher. Ailleurs — conhost.exe, console heritee — la reecriture
    repetee de l'ecran se voit toujours, quel que soit le volume envoye : mieux
    vaut un menu fixe qu'un menu qui clignote. « soft » force l'animation pour
    qui la prefere malgre tout.
    """
    if MENU_ANIM == "off":
        return False
    if MENU_ANIM == "soft":
        return not _legacy_console()
    return _compositing_terminal() and not _legacy_console()


def _anim_cadence():
    """Delai et pas de la trainee, adaptes au terminal.

    Une console Windows en mode restreint ne connait pas l'affichage
    synchronise et repeint par appels Win32, beaucoup plus lents : on y espace
    les images et on allonge le pas pour garder la meme vitesse apparente.
    """
    if not _sync_supported():
        return MENU_ANIM_DELAY * 2.0, MENU_ANIM_STEP * 2
    return MENU_ANIM_DELAY, MENU_ANIM_STEP


# ── BORDURE TOURNANTE (trainee lumineuse) ─────────────────
def _lit_border_render(panel, width: int, border_color: str, phase: int, tail: int = 10) -> Text:
    """Redessine le panneau avec une trainee qui parcourt sa bordure.

    La bordure reste TOUJOURS tracee : seule son intensite change sous la
    trainee. Effacer les caracteres eteints (ce que faisait la version
    precedente) faisait disparaitre puis reapparaitre le cadre a chaque
    image, ce qui donnait un clignotement permanent des categories.
    """
    opts = console.options.update(width=width)
    lines = console.render_lines(panel, opts, pad=False)
    h = len(lines)
    w = sum(len(seg.text) for seg in lines[0]) if lines else width

    top_len, right_len, bottom_len, left_len = w, max(0, h - 2), w, max(0, h - 2)
    perim_len = max(1, top_len + right_len + bottom_len + left_len)
    lit = {(phase + k) % perim_len for k in range(tail)}
    # Juste devant la trainee, une amorce a peine plus claire adoucit l'entree
    # et la sortie de la lumiere au lieu d'un bord net qui « saute ».
    halo = {(phase - 1) % perim_len, (phase + tail) % perim_len}
    # La trainee change de COULEUR et pas seulement d'intensite : « gras » et
    # « attenue » sur une meme teinte sont invisibles sur beaucoup de consoles,
    # et le point lumineux ne se distinguait plus du reste du cadre.
    glow = th()["accent"]

    lit_style  = f"bold {glow}"
    halo_style = f"bold {border_color}"

    # Les caracteres consecutifs de meme style sont regroupes en un seul run.
    # Sans ce regroupement, chaque caractere du panneau portait son propre code
    # couleur ANSI : ~2800 codes et 19 Ko par image, un volume que le terminal
    # n'arrivait pas a reecrire sans scintiller.
    out = Text()
    run_chars, run_style = [], None

    def flush():
        nonlocal run_chars, run_style
        if run_chars:
            out.append("".join(run_chars), style=run_style)
            run_chars = []

    def emit(ch, style):
        nonlocal run_chars, run_style
        if run_chars and style == run_style:
            run_chars.append(ch)
            return
        flush()
        run_style = style
        run_chars = [ch]

    for r, segs in enumerate(lines):
        edge_row = (r == 0 or r == h - 1)
        col = 0
        for seg in segs:
            style_str = str(seg.style) if seg.style else ""
            text = seg.text
            # Contenu interieur : recopie d'un bloc, aucun caractere de bordure.
            if not edge_row and col > 0 and col + len(text) < w:
                flush()
                out.append(text, style=seg.style)
                col += len(text)
                continue

            for ch in text:
                idx = None
                if r == 0 and style_str == border_color:
                    idx = col
                elif r == h - 1 and style_str == border_color:
                    idx = top_len + right_len + (w - 1 - col)
                elif col == w - 1 and 0 < r < h - 1:
                    idx = top_len + (r - 1)
                elif col == 0 and 0 < r < h - 1:
                    idx = top_len + right_len + bottom_len + (h - 2 - r)

                if idx is None:
                    emit(ch, seg.style)
                elif idx in lit:
                    emit(ch, lit_style)
                elif idx in halo:
                    emit(ch, halo_style)
                else:
                    emit(ch, border_color)
                col += 1
        flush()
        out.append("\n")
    return out


def _spin_panel_render(title: str, color: str, items: list, width: int,
                        border_color: str, phase: int, tail: int = 10, query: str = ""):
    panel = _make_panel(title, color, items, width=width, border_color=border_color, query=query)
    if not _anim_active():
        return panel
    return _lit_border_render(panel, width, border_color, phase, tail)

def _terminal_height():
    try:
        return console.size.height
    except Exception:
        return 24


def _compact_menu_parts(cats, width, typed="", col_width=24,
                        phase=0, framed=False):
    """Menu dense : les modules sont listes en grille. `col_width` se resserre
    quand il faut gagner des lignes.

    `framed` entoure l'ensemble des categories d'un cadre unique parcouru par
    la trainee lumineuse : les panneaux par categorie coutent deux lignes
    chacun, un seul cadre n'en coute que deux au total.
    """
    pri, dim = th()["primary"], th()["dim_col"]
    per_row = max(2, min(7, (width - 4) // col_width))
    parts = []
    fav_bar = _favorites_bar(width)
    if fav_bar:
        parts.append(Align.center(fav_bar))
    for title, color, items in cats:
        grid = Table.grid(padding=(0, 1))
        for _ in range(per_row):
            # no_wrap est indispensable : sans lui un libelle trop long est
            # replie sur une seconde ligne au lieu d'etre tronque, et la
            # hauteur du menu double sur une fenetre etroite.
            grid.add_column(width=col_width, overflow="ellipsis", no_wrap=True)
        entries = [Text.assemble((f"{code} ", f"bold {color}" if _item_matches(typed, code, label) else dim),
                                  (label, "white" if _item_matches(typed, code, label) else dim))
                   for code, label in items]
        for i in range(0, len(entries), per_row):
            chunk = entries[i:i + per_row]
            grid.add_row(*(chunk + [Text("")] * (per_row - len(chunk))))
        parts.append(Align.center(Text(f"── {title} ──", style=f"bold {color}")))
        parts.append(Align.center(grid))

    if not framed:
        return parts

    border = th()["border"]
    box_w = max(24, min(width - 2, per_row * (col_width + 1) + 3))
    count = sum(1 for _, _, items in cats for code, _ in items if code != "00")
    panel = Panel(Group(*parts), border_style=border, box=_menu_box(),
                  width=box_w, padding=(0, 1),
                  title=Text(f"/ {count} MODULES \\", style=f"bold {border}"),
                  title_align="center")
    if not _anim_active():
        return [Align.center(panel)]
    return [Align.center(_lit_border_render(panel, box_w, border, phase, tail=16))]


def _menu_footer_parts(cats, typed, pri, dim, slim=False):
    parts = [Align.center(Text(f"{t('prompt')}{typed}", style=f"bold {pri}"))]
    if not slim:
        parts.append(Align.center(_menu_footer_hint(cats, typed, dim)))
    parts.append(Align.center(_live_gauge_text(dim)))
    return parts


def _compact_menu_body(cats, width, typed=""):
    pri, dim = th()["primary"], th()["dim_col"]
    parts = [Align.center(Text(f"/ {DISPLAY_NAME.upper()} \\  {VERSION}",
                               style=f"bold {pri}"))]
    parts += _compact_menu_parts(cats, width, typed)
    parts += _menu_footer_parts(cats, typed, pri, dim)
    return Group(*parts)


# En dessous de cette largeur, un panneau tronque trop de libelles pour rester
# lisible : on renonce alors a la rangee unique.
MIN_ROW_PANEL_W = 29


def _row_panels_width(cats, panel_w=None) -> int:
    """Largeur minimale pour aligner toutes les categories sur une rangee."""
    return len(cats) * MIN_ROW_PANEL_W + (len(cats) - 1) + 2


def _row_panel_width(cats, width, panel_w) -> int:
    """Largeur de chaque panneau en rangee unique.

    Elle se resserre jusqu'a MIN_ROW_PANEL_W pour absorber les quelques
    colonnes manquantes : une largeur figee faisait rater cette disposition —
    pourtant la mieux adaptee aux ecrans larges — a un terminal auquel il ne
    manquait qu'une seule colonne.
    """
    n = max(1, len(cats))
    available = (width - (n - 1) - 2) // n
    return max(MIN_ROW_PANEL_W, min(panel_w, available))


def _panel_menu_parts(cats, width, wide, panel_w, phase, typed="",
                      slim_footer=False, tight=False, single_row=False):
    """Menu en panneaux encadres. `tight` retire les separateurs decoratifs :
    trois lignes de gagnees, ce qui permet de garder un cadre par categorie
    (et donc la trainee lumineuse) sur une fenetre un peu basse.

    `single_row` aligne les cinq categories cote a cote. La disposition
    historique empile SYSTEME au-dessus des quatre autres et depasse 45 lignes ;
    sur un ecran large, une seule rangee n'en occupe qu'une vingtaine et permet
    de garder les cadres par categorie la ou il fallait sinon tout tasser dans
    une grille sans bordures.
    """
    borders = [th()["border"]] * len(cats)
    pri = th()["primary"]
    dim = th()["dim_col"]

    parts = []
    fav_bar = _favorites_bar(width)
    if fav_bar:
        parts.append(Align.center(fav_bar))

    if single_row:
        row_w = _row_panel_width(cats, width, panel_w)
        grid = Table.grid(padding=(0, 1))
        grid.add_row(*[
            _spin_panel_render(*cats[i], row_w, borders[i], phase, query=typed)
            for i in range(len(cats))
        ])
        parts.append(Align.center(grid))
        if not tight:
            parts.append(Align.center(_neon_line(width)))
        parts += _menu_footer_parts(cats, typed, pri, dim, slim_footer)
        return parts

    parts.append(Align.center(_spin_panel_render(*cats[0], panel_w, borders[0],
                                                 phase, query=typed)))
    if not tight:
        parts.append(Align.center(_neon_line(width)))
        parts.append(Align.center(Text(". " * 24, style=dim)))

    if wide:
        grid = Table.grid(padding=(0, 1))
        grid.add_row(
            _spin_panel_render(*cats[3], panel_w, borders[3], phase, query=typed),
            _spin_panel_render(*cats[2], panel_w, borders[2], phase, query=typed),
            _spin_panel_render(*cats[4], panel_w, borders[4], phase, query=typed),
            _spin_panel_render(*cats[1], panel_w, borders[1], phase, query=typed),
        )
        parts.append(Align.center(grid))
    else:
        top = Table.grid(padding=(0, 1))
        top.add_row(
            _spin_panel_render(*cats[3], panel_w, borders[3], phase, query=typed),
            _spin_panel_render(*cats[4], panel_w, borders[4], phase, query=typed),
        )
        middle = Table.grid(padding=(0, 1))
        middle.add_row(
            _spin_panel_render(*cats[2], panel_w, borders[2], phase, query=typed),
            _spin_panel_render(*cats[1], panel_w, borders[1], phase, query=typed),
        )
        parts.append(Align.center(top))
        if not tight:
            parts.append(Align.center(Text(". " * 24, style=dim)))
        parts.append(Align.center(middle))

    if not tight:
        parts.append(Align.center(Text("-" * min(width - 12, 112), style=dim)))
    parts += _menu_footer_parts(cats, typed, pri, dim, slim_footer)
    return parts


def _spin_menu_body(cats, width, wide, panel_w, phase, typed=""):
    if _terminal_height() < 40:
        return _compact_menu_body(cats, width, typed)
    return Group(*_panel_menu_parts(cats, width, wide, panel_w, phase, typed))


# ── CHOIX DE LA MISE EN PAGE ──────────────────────────────
# Du plus aere au plus dense. Le menu doit tenir en entier dans la fenetre :
# des qu'il la depasse, le terminal se met a defiler et l'ecran clignote a
# chaque rafraichissement de l'animation.
# Le logo du pseudo est ce que l'on sacrifie en DERNIER : c'est la signature de
# l'outil, et la faire disparaitre pour gagner deux lignes donnait l'impression
# que le pseudo s'effacait tout seul « apres certaines manipulations » (un
# changement de theme ou de langue suffit a rejouer ce calcul). On resserre donc
# d'abord le menu jusqu'au bout, et seulement ensuite la banniere.
MENU_LAYOUTS = (
    # banniere, mode, largeur de colonne, pied reduit, cadre anime
    ("full",  "panels",  24, False, False),
    ("full",  "row",     24, False, False),
    ("slim",  "panels",  24, False, False),
    ("slim",  "row",     24, False, False),
    ("mini",  "row",     24, False, False),
    ("slim",  "tight",   24, False, False),
    ("slim",  "tight",   24, True,  False),
    ("slim",  "compact", 24, False, True),
    ("slim",  "compact", 20, False, True),
    ("slim",  "compact", 16, False, True),
    ("slim",  "compact", 16, False, False),
    ("slim",  "compact", 13, False, False),
    ("slim",  "compact", 13, True,  False),
    ("small", "compact", 13, False, False),
    ("small", "compact", 13, True,  False),
    ("mini",  "compact", 13, True,  False),
)
# fits=False signale qu'aucune mise en page ne rentre : l'appelant coupe alors
# l'animation plutot que de faire defiler l'ecran a chaque image.
_LAYOUT_CACHE = {"key": None, "layout": MENU_LAYOUTS[0], "fits": True}


def _menu_frame(cats, width, wide, panel_w, phase, typed, layout):
    banner_level, menu_mode, col_width, slim_footer, framed = layout
    parts = list(_banner_parts(width, banner_level))
    if menu_mode in ("panels", "tight", "row"):
        parts += _panel_menu_parts(cats, width, wide, panel_w, phase, typed,
                                   slim_footer, tight=(menu_mode == "tight"),
                                   single_row=(menu_mode == "row"))
    else:
        pri, dim = th()["primary"], th()["dim_col"]
        parts += _compact_menu_parts(cats, width, typed, col_width, phase, framed)
        parts += _menu_footer_parts(cats, typed, pri, dim, slim_footer)
    return Group(*parts)


def _frame_height(renderable, width) -> int:
    try:
        opts = console.options.update(width=width, height=None)
        return len(console.render_lines(renderable, opts, pad=False))
    except Exception:
        return 0


def _pick_menu_layout(cats, width, wide, panel_w, typed=""):
    """Retient la mise en page la plus riche qui tient dans la hauteur.

    Le calcul demande un rendu d'essai, trop couteux a refaire a chaque image :
    il n'est relance que si la taille de la fenetre, le theme ou le nombre de
    modules affiches a change.
    """
    height = _terminal_height()
    key = (width, height, THEME_NAMES[CURRENT_THEME_IDX], len(FAVORITES),
           sum(len(items) for _, _, items in cats), LANG, MENU_ANIM)
    if _LAYOUT_CACHE["key"] == key:
        return _LAYOUT_CACHE["layout"]

    chosen, fits = MENU_LAYOUTS[-1], False
    for layout in MENU_LAYOUTS:
        # Une rangee unique ne se tente que si l'ecran est assez large pour
        # aligner toutes les categories sans les tronquer.
        if layout[1] == "row" and width < _row_panels_width(cats, panel_w):
            continue
        frame = _menu_frame(cats, width, wide, panel_w, 0, typed, layout)
        # Une ligne de marge : le curseur laisse par Live occupe la derniere.
        if _frame_height(frame, width) <= height - 1:
            chosen, fits = layout, True
            break

    _LAYOUT_CACHE["key"] = key
    _LAYOUT_CACHE["layout"] = chosen
    _LAYOUT_CACHE["fits"] = fits
    return chosen


def _layout_fits() -> bool:
    return bool(_LAYOUT_CACHE["fits"])


def _spin_menu_intro(cats, width, wide, panel_w):
    if not _anim_active():
        return
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
    """Affichage unique du menu, hors animation (sortie redirigee, --run...)."""
    clr()
    cats = get_cats()
    width = _screen_width()
    wide = width >= 145
    panel_w = 31 if wide else 34

    if spin_intro:
        _spin_menu_intro(cats, width, wide, panel_w)

    layout = _pick_menu_layout(cats, width, wide, panel_w, typed)
    console.print(_menu_frame(cats, width, wide, panel_w, 0, typed, layout))

_WIN_ARROWS  = {"H": "<UP>", "P": "<DOWN>", "K": "<LEFT>", "M": "<RIGHT>"}
_UNIX_ARROWS = {"A": "<UP>", "B": "<DOWN>", "C": "<RIGHT>", "D": "<LEFT>"}
_ARROW_TOKENS = set(_WIN_ARROWS.values())
KONAMI_SEQUENCE = ["<UP>", "<UP>", "<DOWN>", "<DOWN>",
                   "<LEFT>", "<RIGHT>", "<LEFT>", "<RIGHT>", "b", "a"]
KONAMI_TRIGGER = "\x00konami"


def keytest():
    """Affiche ce que le terminal envoie reellement pour chaque touche.
    Sert a diagnostiquer les touches flechees quand le secret ne repond pas."""
    console.print()
    console.print(f"  [{th()['primary']}]Test clavier[/{th()['primary']}] — appuie sur les "
                  f"fleches puis sur B et A.  [dim](Ctrl+C pour quitter)[/dim]")
    console.print(f"  [dim]Plateforme : {os.name} · Python {sys.version.split()[0]}[/dim]")
    console.print()

    if os.name == "nt":
        import msvcrt
        try:
            while True:
                if not msvcrt.kbhit():
                    time.sleep(0.01)
                    continue
                ch = msvcrt.getwch()
                if ch == "\x03":
                    raise KeyboardInterrupt
                if ch in ("\x00", "\xe0"):
                    code = msvcrt.getwch()
                    token = _WIN_ARROWS.get(code, "")
                    raw_print(f"  prefixe={ch!r}  code={code!r}  -> token={token!r}"
                              f"{'   <-- NON RECONNU' if not token else ''}")
                else:
                    raw_print(f"  char={ch!r}  (U+{ord(ch):04X})  -> token={ch.lower()!r}")
        except KeyboardInterrupt:
            console.print()
            info("Test termine.")
        return

    import select, termios, tty
    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        while True:
            ready, _, _ = select.select([sys.stdin], [], [], 0.05)
            if not ready:
                continue
            ch = sys.stdin.read(1)
            if ch == "\x03":
                raise KeyboardInterrupt
            if ch == "\x1b":
                seq = ""
                for _ in range(2):
                    r, _, _ = select.select([sys.stdin], [], [], 0.05)
                    if not r:
                        break
                    seq += sys.stdin.read(1)
                token = _UNIX_ARROWS.get(seq[1]) if len(seq) == 2 else None
                raw_print(f"  ESC + {seq!r}  -> token={token!r}"
                          f"{'   <-- NON RECONNU' if not token else ''}")
            else:
                raw_print(f"  char={ch!r}  (U+{ord(ch):04X})  -> token={ch.lower()!r}")
    except KeyboardInterrupt:
        console.print()
        info("Test termine.")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)


def _animated_menu_input():
    if not sys.stdin.isatty():
        _render_menu_frame("")
        raw = console.input(f"[bold {th()['primary']}]{t('prompt')}[/bold {th()['primary']}]").strip()
        if raw:
            CMD_HISTORY.append(raw)
        return raw

    typed = ""
    phase = 0
    last_spin = 0.0
    term_state = None

    konami = deque(maxlen=len(KONAMI_SEQUENCE))
    konami_hit = False

    if os.name == "nt":
        import msvcrt

        def read_key():
            if not msvcrt.kbhit():
                return None
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):
                # Une touche flechee arrive en deux temps : le prefixe puis le
                # code. Le second est toujours dispo, on le lit sans tester
                # kbhit() — sinon la flechee est perdue et la sequence cassee.
                return _WIN_ARROWS.get(msvcrt.getwch(), "")
            return ch

        def read_follow():
            deadline = time.monotonic() + 0.05
            while time.monotonic() < deadline:
                if msvcrt.kbhit():
                    return msvcrt.getwch()
                time.sleep(0.002)
            return None
    else:
        import select
        import termios
        import tty

        fd = sys.stdin.fileno()
        term_state = termios.tcgetattr(fd)
        tty.setcbreak(fd)

        def read_key():
            ready, _, _ = select.select([sys.stdin], [], [], 0)
            if not ready:
                return None
            return sys.stdin.read(1)

        def read_follow():
            # La suite d'une sequence ESC peut arriver quelques ms plus tard :
            # avec un timeout nul on lisait parfois dans le vide.
            ready, _, _ = select.select([sys.stdin], [], [], 0.05)
            if not ready:
                return None
            return sys.stdin.read(1)

    def note_konami(token):
        nonlocal konami_hit
        konami.append(token)
        if list(konami) == KONAMI_SEQUENCE:
            konami.clear()
            konami_hit = True

    def handle_key(ch):
        nonlocal typed
        if ch in ("\r", "\n"):
            raw = typed.strip()
            if raw:
                CMD_HISTORY.append(raw)
            return raw
        if ch == "\x03":
            raise KeyboardInterrupt
        if ch in ("\x08", "\x7f"):
            typed = typed[:-1]
        elif ch in _ARROW_TOKENS:
            note_konami(ch)
        elif ch == "\x1b":
            # Sequence ESC [ A/B/C/D des touches flechees (Unix, et Windows
            # Terminal quand l'entree VT est active).
            seq = ""
            for _ in range(2):
                nxt = read_follow()
                if nxt is None:
                    break
                seq += nxt
            if len(seq) == 2 and seq[0] in ("[", "O"):
                token = _UNIX_ARROWS.get(seq[1])
                if token:
                    note_konami(token)
        elif ch.isprintable():
            typed += ch
            note_konami(ch.lower())
        return None

    try:
        clr()
        width = _screen_width()
        wide = width >= 145
        panel_w = 31 if wide else 34
        cats = get_cats()
        layout = _pick_menu_layout(cats, width, wide, panel_w)
        body = _menu_frame(cats, width, wide, panel_w, phase, typed, layout)

        # Sans animation a jouer, on se passe entierement de Live : celui-ci
        # n'apporterait que ses effets de bord (ecran alternatif, curseur
        # masque, stdout redirige), dont un curseur qui reste invisible dans
        # les modules sur les consoles qui restaurent mal l'etat en quittant
        # l'ecran alternatif. Idem si la fenetre est trop petite pour afficher
        # le menu entier. On redessine alors uniquement a la frappe.
        if not _layout_fits() or not _anim_active():
            console.show_cursor(True)
            console.print(body)

            def repaint():
                _sync_write(_SYNC_BEGIN)
                try:
                    clr()
                    console.print(_menu_frame(cats, width, wide, panel_w,
                                              phase, typed, layout))
                finally:
                    _sync_write(_SYNC_END)

            last_size = (width, _terminal_height())
            last_check = time.monotonic()
            while True:
                ch = read_key()
                if ch is None:
                    # Sans animation, rien ne redessine le menu de lui-meme :
                    # il faut surveiller la taille de la fenetre, sinon un
                    # passage en plein ecran laisse la mise en page compacte
                    # calculee pour l'ancienne taille. On interroge le systeme
                    # trois fois par seconde, pas a chaque tour de boucle.
                    now = time.monotonic()
                    if now - last_check >= 0.3:
                        last_check = now
                        size = (_screen_width(), _terminal_height())
                        if size != last_size:
                            last_size = size
                            width = size[0]
                            wide = width >= 145
                            panel_w = 31 if wide else 34
                            cats = get_cats()
                            layout = _pick_menu_layout(cats, width, wide,
                                                       panel_w, typed)
                            if _layout_fits() and _anim_active():
                                # La fenetre permet de nouveau l'animation.
                                return _animated_menu_input()
                            repaint()
                    time.sleep(0.02)
                    continue
                if not ch:
                    continue
                result = handle_key(ch)
                if result is not None:
                    return result
                if konami_hit:
                    return KONAMI_TRIGGER
                repaint()

        last_clock = ""
        # La banniere fait partie du contenu anime : imprimee avant le Live,
        # elle poussait le menu hors de l'ecran et forcait un defilement a
        # chaque image. vertical_overflow="crop" garantit qu'aucune image ne
        # depasse, meme si la fenetre est redimensionnee entre deux mesures.
        # auto_refresh=False est essentiel : par defaut Rich relance un rendu
        # complet MENU_ANIM_FPS fois par seconde meme quand rien n'a change
        # (mesure : 300 Ko envoyes au terminal en deux secondes d'inactivite).
        # On ne redessine desormais que sur changement reel.
        #
        # screen=True bascule sur le buffer alternatif du terminal (comme less
        # ou htop) : l'ecran a une taille fixe, aucun defilement n'est possible
        # et le curseur ne peut plus pousser le contenu vers le haut. Rich
        # l'ignore purement et simplement si la console n'a pas le mode VT
        # actif (console.py : `if self.is_terminal and not self.legacy_windows`),
        # d'ou le repli sur l'affichage non anime plus bas.
        with Live(body, console=console, refresh_per_second=MENU_ANIM_FPS,
                  transient=False, vertical_overflow="crop",
                  auto_refresh=False, screen=_alt_screen_usable()) as live:
            while True:
                dirty = False

                while True:
                    ch = read_key()
                    if ch is None:
                        break
                    if ch:
                        result = handle_key(ch)
                        if result is not None:
                            return result
                        if konami_hit:
                            return KONAMI_TRIGGER
                        dirty = True

                current_width = _screen_width()
                if current_width != width:
                    width = current_width
                    wide = width >= 145
                    panel_w = 31 if wide else 34
                    cats = get_cats()
                    dirty = True
                new_layout = _pick_menu_layout(cats, width, wide, panel_w)
                if new_layout != layout:
                    layout = new_layout
                    dirty = True
                if not _layout_fits():
                    # La fenetre a retreci sous le minimum : on sort du mode
                    # anime plutot que de laisser l'ecran defiler.
                    break

                now = time.monotonic()
                anim_delay, anim_step = _anim_cadence()
                if _anim_active() and now - last_spin >= anim_delay:
                    phase += anim_step
                    last_spin = now
                    dirty = True

                # L'horloge et les jauges du bas ne justifient PAS de redessiner
                # l'ecran a elles seules : quand l'animation est coupee, ce
                # seul rafraichissement produisait un flash complet toutes les
                # secondes — le « clignotement » persistant, y compris pour qui
                # avait desactive l'animation. Elles suivent donc les images de
                # l'animation quand il y en a une, et restent figees sinon
                # jusqu'a la prochaine touche (le menu est reaffiche a chaque
                # retour de module, l'heure ne reste jamais fausse longtemps).
                if _anim_active():
                    clock = datetime.now().strftime("%H:%M:%S")
                    if clock != last_clock:
                        last_clock = clock
                        dirty = True

                if dirty:
                    _synced_update(live, _menu_frame(cats, width, wide, panel_w,
                                                     phase, typed, layout))

                time.sleep(0.02)

        return _animated_menu_input()
    finally:
        if term_state is not None:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, term_state)
        # Rich montre le curseur avant de quitter l'ecran alternatif ; les
        # consoles qui restaurent l'etat d'affichage a ce moment-la peuvent le
        # laisser masque, et l'on saisit alors a l'aveugle dans les modules.
        try:
            console.show_cursor(True)
        except Exception:
            pass

def draw_menu() -> str:
    return _animated_menu_input()

def section(label: str, color: str):
    clr()
    banner()
    panel = Panel(
        Text(f">>> {label.upper()}", style=f"bold {color}"),
        border_style=color,
        box=th()["box"],
        expand=False,
        padding=(0, 4),
    )
    if sys.stdin.isatty() and _anim_active():
        try:
            width = _screen_width()
            with Live(Align.center(panel), console=console,
                      refresh_per_second=30, transient=True) as live:
                for phase in range(0, 18, 3):
                    live.update(Align.center(_lit_border_render(panel, width, color, phase, tail=6)))
                    time.sleep(0.02)
        except Exception:
            pass
    console.print(Align.center(panel))
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
    _save_prefs()          # le choix survit a la fermeture

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
    try:
        t_ui.add_row("Processus actifs", str(len(psutil.pids())))
    except Exception:
        pass
    try:
        n_users = len(psutil.users())
        t_ui.add_row("Sessions ouvertes", str(n_users))
    except Exception:
        pass
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
    critical = []
    for p in psutil.disk_partitions():
        try:
            u = psutil.disk_usage(p.mountpoint)
            t_ui.add_row(p.device, p.fstype, f"{u.total/1e9:.1f}G",
                         f"{u.used/1e9:.1f}G", f"{u.free/1e9:.1f}G",
                         f"{pct_bar(u.percent, 12)} {u.percent}%")
            if u.percent >= 90:
                critical.append((p.device, u.percent))
        except PermissionError: pass
    try:
        dk = psutil.disk_io_counters()
        if dk:
            console.print()
            info(f"Lecture totale : {dk.read_bytes/1e9:.2f} GB  |  Écriture totale : {dk.write_bytes/1e9:.2f} GB")
    except Exception: pass
    console.print(t_ui)
    if critical:
        noms = ", ".join(f"{d} ({p:.0f}%)" for d, p in critical)
        warn(f"Espace disque critique (≥90%) : {noms}")

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
            f.write("\n[DISQUES]\n")
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
    if not sensitive_notice("IP publique, localisation, FAI"):
        return
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
    host = ask_host(col, "Host", "8.8.8.8")
    if not host:
        return
    count = ask_int(col, "Pings", 4, 1, 100)
    console.print(f"\n[dim {col}]Ping → {esc(host)}  (x{count})...[/dim {col}]\n")
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    try:
        subprocess.run(["ping", param, str(count), host], timeout=max(30, count * 3))
    except FileNotFoundError:
        error("La commande ping est introuvable sur ce systeme.")
    except subprocess.TimeoutExpired:
        error("Timeout.")

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
    host = ask_host(col, "Host", "localhost")
    if not host:
        return
    raw   = console.input(f"[{col}]  Ports [dim](ex: 80,443,8080 ou vide=communs)[/dim] ❯ [/{col}]").strip()
    known = { 21:"FTP", 22:"SSH", 23:"Telnet", 25:"SMTP", 53:"DNS", 80:"HTTP",
              110:"POP3", 143:"IMAP", 443:"HTTPS", 3306:"MySQL", 3389:"RDP",
              5432:"PgSQL", 8080:"HTTP-Alt", 27017:"MongoDB" }
    # Ports bornes a 1-65535 et liste plafonnee : sans ca, une saisie large
    # ouvrirait autant de sockets que de ports demandes.
    if raw:
        ports = sorted({int(p) for p in raw.split(",")
                        if p.strip().isdigit() and 1 <= int(p) <= 65535})[:1024]
        if not ports:
            error("Aucun port valide (attendu : 1-65535, separes par des virgules).")
            return
    else:
        ports = list(known.keys())
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
    if not sensitive_notice("appareils et IP du réseau local"):
        return
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

            t_ui = themed_table(title=f"[dim]{sym('live')} Live — {datetime.now().strftime('%H:%M:%S')}[/dim]", border_style=col)
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
    t_ui.add_row("BLAKE2b", hashlib.blake2b(enc).hexdigest())
    t_ui.add_row("CRC32",   f"{zlib.crc32(enc):08x}")
    console.print(t_ui)

def _secure_shuffle(seq):
    items = list(seq)
    for i in range(len(items) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        items[i], items[j] = items[j], items[i]
    return items


def password_gen():
    import math
    col = th()["cat_uti"]
    if not sensitive_notice("mots de passe générés en clair"):
        return
    n = ask_int(col, "Longueur", 18, 8, 128)

    sets = {
        "alpha": string.ascii_letters,
        "digits": string.digits,
        "spec": "!@#$%^&*()-_=+[]{}|;:,.<>?"
    }
    chars = sets["alpha"] + sets["digits"] + sets["spec"]
    entropy = n * math.log2(len(chars))

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
        pwd = (secrets.choice(sets["alpha"].upper()) +
               secrets.choice(sets["digits"]) +
               secrets.choice(sets["spec"]) +
               ''.join(secrets.choice(chars) for _ in range(max(0, n - 3))))
        pwd = ''.join(_secure_shuffle(pwd))
        sc = strength(pwd)
        t_ui.add_row(str(i+1), pwd, f"{pct_bar(sc, 10)} {sc}/100")
    console.print(t_ui)
    info(f"Genere avec `secrets` (CSPRNG) — entropie ~{entropy:.0f} bits par mot de passe.")
    crack_seconds = (2 ** entropy) / 1e10 / 2   # 10^10 tentatives/s hors ligne, cassage moyen ≈ moitie de l'espace
    info(f"Temps de cassage estime hors ligne (10^10 tentatives/s) : {_human_duration(crack_seconds)}")

def pass_checker():
    col = th()["cat_uti"]
    console.print(f"[{col}]  Mot de passe à tester [dim](saisie masquée)[/dim][/{col}]")
    try:
        pwd = getpass.getpass("  ❯ ")
    except (EOFError, KeyboardInterrupt):
        info("Annulé.")
        return
    if not pwd:
        info("Aucune saisie.")
        return
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

    blacklisted = pwd.lower() in COMMON_PASSWORDS
    if blacklisted:
        score = min(score, 10)
        t_ui.add_row("Liste noire", "[bold red]✘ TROP COURANT[/bold red]",
                     "[red]plafonne[/red]")
    else:
        t_ui.add_row("Liste noire", "[green]✔ absent[/green]", "[dim]—[/dim]")

    t_ui.add_row("─"*28, "─"*13, "─"*8)
    lvl = "FAIBLE" if score < 40 else "MOYEN" if score < 70 else "FORT" if score < 90 else "EXCELLENT"
    lvl_col = "red" if score < 40 else "yellow" if score < 70 else "green" if score < 90 else "bright_green"
    t_ui.add_row("Score Global", f"[{lvl_col}]{lvl}[/{lvl_col}]", f"[bold]{score}/100[/bold]")
    t_ui.add_row("", f"{pct_bar(score, 14)}", "")
    console.print(t_ui)
    if blacklisted:
        warn("Ce mot de passe figure parmi les plus utilisés au monde — change-le immediatement s'il sert reellement.")

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

    if os.name == "nt":
        temp_dirs = [os.environ.get("TEMP"), os.environ.get("TMP")]
        if is_admin():
            temp_dirs.append(os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "Temp"))
    else:
        temp_dirs = [tempfile.gettempdir(), "/var/tmp"]

    # Jamais touche : verrous, sockets et repertoires de session encore vivants.
    PROTECTED = {
        ".x11-unix", ".x11-lock", ".ice-unix", ".font-unix", ".xim-unix",
        ".test-unix", "systemd-private", "snap-private-tmp", "gnupg", "ssh-",
        "pulse-", "dbus-", ".xdg-runtime",
    }

    age_hours = ask_int(col, "Supprimer les fichiers plus vieux que (heures)", 24, 0, 8760)
    cutoff = time.time() - age_hours * 3600

    candidates, total_bytes, skipped = [], 0, 0
    seen_roots = []
    for temp_dir in temp_dirs:
        if not temp_dir or not os.path.isdir(temp_dir):
            continue
        real_root = os.path.realpath(temp_dir)
        if real_root in seen_roots:
            continue
        seen_roots.append(real_root)
        for root, dirs, files in os.walk(temp_dir, topdown=True):
            dirs[:] = [d for d in dirs
                       if not any(d.lower().startswith(p) for p in PROTECTED)]
            for name in files:
                path = os.path.join(root, name)
                # Ne jamais suivre un lien symbolique hors du repertoire temporaire.
                if os.path.islink(path) or not inside(path, real_root):
                    skipped += 1
                    continue
                try:
                    st = os.lstat(path)
                    if st.st_mtime > cutoff:
                        skipped += 1
                        continue
                    candidates.append(path)
                    total_bytes += st.st_size
                except OSError:
                    skipped += 1

    if not candidates:
        info(f"Rien a supprimer ({skipped} element(s) ignore(s) : trop recents, proteges ou verrouilles).")
        return

    t_ui = themed_table(border_style=col)
    t_ui.add_column("Analyse", style=col, width=32)
    t_ui.add_column("Valeur", style="bold white", width=40)
    t_ui.add_row("Repertoires", ", ".join(seen_roots))
    t_ui.add_row("Fichiers eligibles", str(len(candidates)))
    t_ui.add_row("Espace recuperable", f"{total_bytes / 1e6:.1f} Mo")
    t_ui.add_row("Ignores (recents/proteges)", str(skipped))
    t_ui.add_row("Critere", f"non modifies depuis {age_hours} h")
    console.print(t_ui)

    console.print()
    for path in candidates[:10]:
        raw_print(f"    {path}")
    if len(candidates) > 10:
        console.print(f"  [dim]... et {len(candidates) - 10} autre(s)[/dim]")

    console.print()
    if console.input(
        f"  [{th()['danger']}]Tapez SUPPRIMER pour confirmer ❯ [/{th()['danger']}]"
    ).strip() != "SUPPRIMER":
        info("Operation annulee, aucun fichier supprime.")
        return

    removed, freed, failed = 0, 0, 0
    for path in candidates:
        try:
            size = os.lstat(path).st_size
            os.remove(path)
            removed += 1
            freed += size
        except OSError:
            failed += 1

    # Repertoires devenus vides seulement, jamais les racines.
    for real_root in seen_roots:
        for root, dirs, files in os.walk(real_root, topdown=False):
            if os.path.realpath(root) == real_root:
                continue
            try:
                os.rmdir(root)
            except OSError:
                pass

    success(f"{removed} fichier(s) supprime(s), {freed / 1e6:.1f} Mo liberes.")
    if failed:
        info(f"{failed} fichier(s) verrouille(s) ou proteges — ignores.")

# ═══════════════════════════════════════════════════════
#  FEATURES AVANCÉES
# ═══════════════════════════════════════════════════════

def traceroute():
    col  = th()["cat_adv"]
    host = ask_host(col, "Cible", "8.8.8.8")
    if not host:
        return
    console.print(f"\n[dim {col}]Traceroute → {esc(host)}...[/dim {col}]\n")
    cmd = (["tracert", host] if platform.system().lower() == "windows"
           else ["traceroute", "-m", "20", host])
    try:
        subprocess.run(cmd, timeout=120)
    except FileNotFoundError:
        error("traceroute/tracert non disponible sur ce système.")
    except subprocess.TimeoutExpired:
        error("Timeout (120 s).")

def whois_geoip():
    col  = th()["cat_adv"]
    host = ask_host(col, "IP ou Domaine")
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
    # HTTPS obligatoire : en HTTP clair, contenu et resultat seraient
    # manipulables par tout intermediaire reseau.
    TEST_URL = "https://speed.cloudflare.com/__down?bytes=1048576"
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
            # Lecture plafonnee : un serveur hostile pourrait renvoyer
            # plusieurs Go et saturer la memoire.
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = read_capped(resp, 16 * 1024 * 1024)
            duration = time.time() - start; size_mb = len(data) / 1e6
            t_ui.add_row(f"Download ({label})",
                         f"[bold green]{size_mb/duration*8:.2f} Mbps[/bold green]  [dim]({size_mb:.2f}MB en {duration:.1f}s)[/dim]")
            break
        except Exception as e: t_ui.add_row(f"Download ({label})", f"[red]Erreur : {esc(e)}[/red]")
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
    names = visible_theme_names()
    current = THEME_NAMES[CURRENT_THEME_IDX]
    pos = names.index(current) if current in names else -1
    CURRENT_THEME_IDX = THEME_NAMES.index(names[(pos + 1) % len(names)])
    success(f"Thème : [bold]{old_name}[/bold] → [bold]{th()['name']}[/bold]")
    _save_prefs()          # le choix survit a la fermeture
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

        t_ui.add_row("[dim]Fichier[/dim]", conf_path, "[dim]—[/dim]", "")
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
            status = "[green]✔ OK[/green]" if ok else "[red]✘ KO[/red]"
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
    log_path = DEFAULT_LOGS.get(choice, os.path.expanduser(choice))

    if not os.path.isfile(log_path):
        error(f"Fichier introuvable : {esc(log_path)}"); return

    n_lines = ask_int(col, "Dernières lignes à afficher", 20, 1, 5000)

    def colorize(line: str) -> str:
        # Le contenu du log est echappe : sans ca, une ligne contenant du
        # balisage Rich (ex: "[/]") etait interpretee — un attaquant capable
        # d'ecrire dans un log pouvait corrompre l'affichage ou declencher
        # une MarkupError qui tuait l'outil.
        line = esc(line)
        l = line.lower()
        if any(k in l for k in ("error","err","fatal","critical","crit","alert","emerg")): return f"[red]{line}[/red]"
        elif any(k in l for k in ("warn","warning")): return f"[yellow]{line}[/yellow]"
        elif any(k in l for k in ("info","notice","debug")): return f"[dim]{line}[/dim]"
        elif any(k in l for k in ("success","ok","started","ready","listening")): return f"[green]{line}[/green]"
        elif any(k in l for k in ("fail","denied","refused","invalid","unauthorized")): return f"[bold red]{line}[/bold red]"
        return line

    console.print(f"\n[dim {col}]  Watching : {log_path}  —  Ctrl+C pour arrêter[/dim {col}]\n")

    try:
        # tail_lines() remonte depuis la fin : `f.readlines()[-n:]`
        # chargerait le fichier ENTIER en RAM.
        # Sur un /var/log/syslog de plusieurs Go, l'outil se faisait tuer par
        # l'OOM killer. tail_lines() remonte depuis la fin du fichier.
        for line in tail_lines(log_path, n_lines):
            console.print(f"  {colorize(line.rstrip())}")
    except PermissionError:
        error(f"Accès refusé à {esc(log_path)} — essayez en root."); return
    except OSError as e:
        error(f"Lecture impossible : {esc(e)}"); return

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line: console.print(f"  [{th()['dim_col']}]{datetime.now().strftime('%H:%M:%S')}[/{th()['dim_col']}]  {colorize(line.rstrip())}")
                else: time.sleep(0.3)
    except KeyboardInterrupt: console.print(f"\n[{col}]  Watcher arrêté.[/{col}]")
    except PermissionError: error("Accès refusé.")

def _run_capture_text(cmd, timeout=10):
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )

    def decode(data):
        if not data:
            return ""
        encodings = ["utf-8-sig", "cp850", "cp437", "cp1252"]
        if os.name == "nt":
            encodings.append("mbcs")
        for encoding in encodings:
            try:
                return data.decode(encoding)
            except (LookupError, UnicodeDecodeError):
                pass
        return data.decode("utf-8", errors="replace")

    return result.returncode, decode(result.stdout), decode(result.stderr)

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
            code, stdout, stderr = _run_capture_text(["sc.exe", "queryex", "type=", "service", "state=", "all"], timeout=10)
            output = stdout or stderr
            if code != 0 and stderr:
                warn(stderr.strip()[:140])
            svc, count = {}, 0

            def add_service(row):
                if not row.get("name"):
                    return 0
                state = row.get("state", "?")
                status = "[green]RUNNING[/green]" if state == "RUNNING" else f"[red]{state}[/red]"
                pid = row.get("pid", "-")
                if not pid or pid == "0":
                    pid = "-"
                t_ui.add_row(
                    row.get("name", "?")[:30],
                    status,
                    row.get("type", "win32")[:10],
                    pid[:8],
                    row.get("display", "?")[:28],
                )
                return 1

            for line in output.splitlines():
                line = line.strip()
                if line.startswith("SERVICE_NAME:"):
                    count += add_service(svc)
                    svc = {"name": line.split(":", 1)[1].strip()}
                elif line.startswith("DISPLAY_NAME:"):
                    svc["display"] = line.split(":", 1)[1].strip()
                elif line.startswith("TYPE"):
                    parts = line.split(":", 1)[1].strip().split(None, 1)
                    svc["type"] = parts[1].lower() if len(parts) > 1 else (parts[0].lower() if parts else "win32")
                elif line.startswith("STATE"):
                    parts = line.split(":", 1)[1].strip().split()
                    svc["state"] = parts[1] if len(parts) > 1 else (parts[0] if parts else "?")
                elif line.startswith("PID"):
                    svc["pid"] = line.split(":", 1)[1].strip()
            count += add_service(svc)
            info(f"{count} services listés.")
        except FileNotFoundError: error("sc.exe non disponible.")
        except subprocess.TimeoutExpired: error("Timeout.")
        except Exception as e: error(f"Erreur : {e}")
    else:
        try:
            code, stdout, stderr = _run_capture_text(["systemctl", "list-units", "--type=service", "--all", "--no-pager", "--plain", "--no-legend"], timeout=10)
            count = 0
            for line in stdout.splitlines():
                parts = line.split()
                if len(parts) < 4: continue
                name, active, sub = parts[0], parts[2], parts[3]
                desc = " ".join(parts[4:])[:28] if len(parts) > 4 else "—"
                status_str = ("[green]▶ active[/green]" if active == "active"
                              else "[red]✘ failed[/red]" if active == "failed"
                              else "[dim]■ inactive[/dim]" if active == "inactive"
                              else f"[yellow]{esc(active)}[/yellow]")
                pid_str = "—"
                try:
                    _, pid_stdout, _ = _run_capture_text(["systemctl", "show", name, "--property=MainPID"], timeout=2)
                    for l2 in pid_stdout.splitlines():
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
        # Le nom part vers systemctl/sc.exe : un nom commencant par '-'
        # deviendrait une OPTION de la commande (injection d'arguments), et
        # les caracteres exotiques casseraient l'affichage.
        if not re.fullmatch(r"[A-Za-z0-9@._\-]{1,128}", action_svc) or action_svc.startswith("-"):
            error("Nom de service invalide.")
            return
        try:
            console.print(Rule(f"[{col}]status : {esc(action_svc)}[/{col}]", style=f"dim {col}"))
            if system == "windows":
                _, query_out, query_err = _run_capture_text(["sc.exe", "queryex", action_svc], timeout=5)
                _, config_out, config_err = _run_capture_text(["sc.exe", "qc", action_svc], timeout=5)
                # raw_print : la sortie d'une commande externe n'est jamais
                # interpretee comme du balisage Rich.
                raw_print((query_out or query_err or "").strip())
                raw_print((config_out or config_err or "").strip())
            else:
                _, stdout, stderr = _run_capture_text(["systemctl", "status", "--no-pager", "--", action_svc], timeout=5)
                raw_print(stdout or stderr)
        except FileNotFoundError: error("Commande systeme non disponible.")
        except subprocess.TimeoutExpired: error("Timeout.")
        except Exception as e: error(f"Erreur : {esc(e)}")

# Motifs de secrets reconnus dans les VALEURS, pas seulement dans les noms.
_SECRET_VALUE_PATTERNS = (
    re.compile(r"^gh[pousr]_[A-Za-z0-9]{20,}$"),              # jetons GitHub
    re.compile(r"^xox[baprs]-[A-Za-z0-9-]{10,}$"),            # jetons Slack
    re.compile(r"^sk-[A-Za-z0-9_\-]{20,}$"),                  # cles style OpenAI
    re.compile(r"^AKIA[0-9A-Z]{16}$"),                        # cles AWS
    re.compile(r"^eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\."),     # JWT
    re.compile(r"^-----BEGIN [A-Z ]*PRIVATE KEY-----"),       # cles privees
    re.compile(r"^[A-Za-z0-9+/]{40,}={0,2}$"),                # base64 long
)


def _looks_secret(value: str) -> bool:
    v = (value or "").strip()
    return bool(v) and any(p.match(v) for p in _SECRET_VALUE_PATTERNS)


def env_inspector():
    col = th()["primary"]
    if not sensitive_notice("variables d'environnement, parfois des secrets"):
        return
    SENSITIVE = {"password","passwd","secret","token","key","api_key","apikey","auth","credential","private","cert","ssl","pass","pwd","session","cookie","signature"}
    filtr = console.input(f"[{col}]  Filtre [dim](sur le NOM, vide = tout afficher)[/dim] ❯ [/{col}]").strip().lower()
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Variable", style=col, width=30)
    t_ui.add_column("Valeur",   style="white", width=56)

    count = masked = 0
    for key, val in sorted(os.environ.items()):
        # Filtre sur le nom uniquement : chercher par valeur serait un
        # oracle sur des variables censees etre masquees.
        if filtr and filtr not in key.lower():
            continue
        is_sensitive = any(s in key.lower() for s in SENSITIVE) or _looks_secret(val)
        if is_sensitive:
            masked += 1
            display_val = f"[red]{'*' * min(max(len(val), 1), 20)}  [dim](masqué)[/dim][/red]"
        else:
            display_val = esc(val[:56])
        t_ui.add_row(esc(key), display_val)
        count += 1

    console.print(t_ui)
    info(f"{count} variable(s) affichée(s), dont {masked} masquée(s).")

def arp_table():
    col = th()["primary"]
    if not sensitive_notice("adresses IP/MAC du réseau local"):
        return
    t_ui = themed_table(border_style=col)
    t_ui.add_column("IP",        style=col, width=20)
    t_ui.add_column("MAC",       style="bold white", width=22)
    t_ui.add_column("Interface", style="dim", width=14)
    t_ui.add_column("Type",      style="dim", width=10)
    t_ui.add_column("Alerte",    width=14)
    entries = []

    if platform.system().lower() == "windows":
        try:
            res = subprocess.run(["arp", "-a"], capture_output=True, text=True, timeout=5, errors="replace")
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
    if not sensitive_notice("connexions réseau actives"):
        return
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Proto",     style=col, width=8)
    t_ui.add_column("Local",     style="white", width=24)
    t_ui.add_column("Distant",   style="white", width=24)
    t_ui.add_column("État",      width=14)
    t_ui.add_column("PID",       style="dim", width=8)
    t_ui.add_column("Process",   style="dim", width=18)
    STATE_COLORS = {"ESTABLISHED": "green", "LISTEN": "cyan", "TIME_WAIT": "yellow", "CLOSE_WAIT": "yellow"}

    stats, rows = {}, []
    try:
        conns = psutil.net_connections(kind="all")
    except (psutil.AccessDenied, PermissionError):
        try:
            conns = psutil.net_connections(kind="inet")
        except (psutil.AccessDenied, PermissionError):
            error("Droits insuffisants pour lister les connexions — relance en root/administrateur.")
            return

    def fmt_addr(addr):
        if not addr:
            return "—"
        if isinstance(addr, str):
            return addr[:24] or "—"
        ip = getattr(addr, "ip", None)
        port = getattr(addr, "port", None)
        if ip is None:
            return str(addr)[:24]
        return f"[{ip}]:{port}" if ":" in str(ip) else f"{ip}:{port}"

    for c in conns:
        status = getattr(c, "status", "NONE") or "NONE"
        stats[status] = stats.get(status, 0) + 1
        laddr = fmt_addr(c.laddr)
        raddr = fmt_addr(c.raddr)
        if getattr(c, "family", None) == getattr(socket, "AF_UNIX", -1):
            proto = "UNIX"
        else:
            proto = "TCP" if c.type == socket.SOCK_STREAM else "UDP"
        pid_str, proc_name = str(c.pid or "—"), "—"
        if c.pid:
            try: proc_name = psutil.Process(c.pid).name()[:18]
            except Exception: pass
        sc = STATE_COLORS.get(status, "white")
        rows.append((proto, esc(laddr), esc(raddr), f"[{sc}]{esc(status)}[/{sc}]",
                     pid_str, esc(proc_name)))

    for row in sorted(rows, key=lambda r: r[3]): t_ui.add_row(*row)
    console.print(t_ui)

def file_hasher():
    col = th()["primary"]
    filepath = console.input(f"[{col}]  Chemin du fichier ❯ [/{col}]").strip()
    filepath = os.path.expanduser(os.path.expandvars(filepath))
    if not os.path.isfile(filepath): error(f"Fichier introuvable : {esc(filepath)}"); return
    size = os.path.getsize(filepath)
    algos = { "MD5": hashlib.md5(), "SHA256": hashlib.sha256(), "SHA512": hashlib.sha512() }
    start = time.time()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                for h in algos.values(): h.update(chunk)
    except Exception as e: error(esc(e)); return

    duration = time.time() - start
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Algo", style=col, width=12)
    t_ui.add_column("Hash", style="bold white", width=70)
    for name, h in algos.items(): t_ui.add_row(name, h.hexdigest())
    t_ui.add_row("─" * 10, "─" * 68)
    t_ui.add_row("Taille", f"{size:,} octets ({size / 1e6:.2f} Mo)".replace(",", " "))
    t_ui.add_row("Duree", f"{duration:.2f} s"
                          + (f"  ({size / duration / 1e6:.1f} Mo/s)" if duration > 0.01 else ""))
    console.print(t_ui)
    info("MD5 est casse (collisions) — n'utilise que SHA-256/SHA-512 pour verifier l'integrite.")

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
                t_ui.add_row(esc(name[-34:]), f"[{s_col}]{esc(status)}[/{s_col}]", esc(next_run[:20]))
                count += 1
            if count == 0:
                t_ui.add_row("—", "[dim]Aucune tâche trouvée[/dim]", "—")
            console.print(t_ui)
            info(f"{count} tâche(s) planifiée(s) trouvée(s).")
        except Exception as e: error(esc(e))
    else:
        try:
            res = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
            console.print(f"[{col}]Crontab Utilisateur :[/{col}]")
            # raw_print : une ligne de crontab contenant du balisage Rich
            # n'est plus interpretee.
            raw_print(res.stdout or "(vide)")
        except FileNotFoundError:
            error("crontab non disponible sur ce système.")
        except subprocess.TimeoutExpired:
            error("Timeout.")
        except Exception as e:
            error(esc(e))

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
    # Format valide avant tout envoi : sans ca, n'importe quelle chaine
    # saisie partirait vers l'API d'un tiers.
    if not re.fullmatch(r"[0-9A-Fa-f]{2}([:-][0-9A-Fa-f]{2}){2,5}", mac):
        error("Format MAC invalide (attendu : AA:BB:CC ou AA:BB:CC:DD:EE:FF).")
        return
    try:
        safe_mac = urllib.parse.quote(mac, safe=":")
        req = urllib.request.Request(f"https://api.macvendors.com/{safe_mac}",
                                     headers={"User-Agent": f"{TOOL_NAME}"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            vendor = read_capped(resp, 8192).decode("utf-8", "replace").strip()
        success(f"Vendeur : [bold white]{esc(vendor)}[/bold white]")
    except urllib.error.HTTPError:
        error("Vendeur introuvable ou requête trop fréquente (API rate limit).")
    except Exception as e:
        error(f"Erreur réseau : {esc(e)}")

BANNER_STYLE_LABELS = {
    "gradient": "Dégradé horizontal",
    "wave":     "Vague (dégradé diagonal)",
    "vertical": "Dégradé vertical (ligne par ligne)",
    "solid":    "Couleur unie du thème",
}


def _available_banner_fonts():
    """Ne garde que les typos que la version de pyfiglet installée sait
    réellement rendre : la liste des polices varie d'une version à l'autre."""
    ok = ["blocks", "auto"]
    try:
        installed = set(pyfiglet.FigletFont.getFonts())
    except Exception:
        installed = set()
    ok += [f for f in BANNER_FONT_CHOICES if f not in ("blocks", "auto") and f in installed]
    return ok


def _preview_banner(font: str, style: str, text: str, width: int = None):
    """Affiche le pseudo avec une typo/style donnés sans les rendre définitifs."""
    global BANNER_FONT, BANNER_STYLE
    saved = (BANNER_FONT, BANNER_STYLE)
    BANNER_FONT, BANNER_STYLE = font, style
    try:
        _gradient_banner(_banner_lines(text, width or _logo_width()))
    except Exception:
        error("Aperçu impossible avec cette typo.")
    finally:
        BANNER_FONT, BANNER_STYLE = saved


def _persist_banner(what: str):
    if _save_name_config():
        success(f"{what} — sauvegardé, repris au prochain lancement.")
    else:
        warn(f"{what} — pour cette session seulement (sauvegarde impossible).")


def _change_pseudo():
    global DISPLAY_NAME
    col = th()["primary"]
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
    console.print()
    _preview_banner(BANNER_FONT, BANNER_STYLE, DISPLAY_NAME)
    console.print()
    _persist_banner(f"Pseudo changé en [bold]{esc(cleaned)}[/bold]")


def _change_banner_font():
    global BANNER_FONT
    col = th()["primary"]
    fonts = _available_banner_fonts()

    while True:
        console.print()
        console.print(f"  [{col}]Typographie du pseudo[/{col}] "
                      f"[dim](* pour voir toutes les typos, vide = retour)[/dim]")
        console.print()
        grid = Table.grid(padding=(0, 3))
        grid.add_column(); grid.add_column(); grid.add_column()
        cells = []
        for i, f in enumerate(fonts, 1):
            marker = "●" if f == BANNER_FONT else "○"
            note = " [dim](dessinée par l'outil)[/dim]" if f == "blocks" else \
                   " [dim](la plus large qui tient)[/dim]" if f == "auto" else ""
            cells.append(f"[dim]{i:2}[/dim] {marker} {f}{note}")
        rows = (len(cells) + 2) // 3
        for r in range(rows):
            grid.add_row(*[cells[r + rows * c] if r + rows * c < len(cells) else ""
                           for c in range(3)])
        console.print(grid)

        pick = console.input(f"\n[{col}]  Typo ❯ [/{col}]").strip()
        if not pick:
            return

        if pick == "*":
            sample = DISPLAY_NAME[:8]
            for f in fonts:
                console.print(f"\n  [dim]── {f} ──[/dim]")
                _preview_banner(f, BANNER_STYLE, sample)
            continue

        if not pick.isdigit() or not (1 <= int(pick) <= len(fonts)):
            error("Numéro invalide.")
            continue

        chosen = fonts[int(pick) - 1]
        console.print()
        _preview_banner(chosen, BANNER_STYLE, DISPLAY_NAME)
        keep = console.input(f"\n[{col}]  Garder cette typo ? [dim][O/n][/dim] ❯ [/{col}]").strip().lower()
        if keep in ("", "o", "oui", "y", "yes"):
            BANNER_FONT = chosen
            _persist_banner(f"Typo : [bold]{chosen}[/bold]")
            return


def _change_banner_style():
    global BANNER_STYLE
    col = th()["primary"]
    console.print()
    for i, style in enumerate(BANNER_STYLES, 1):
        marker = "●" if style == BANNER_STYLE else "○"
        console.print(f"  [dim]{i}[/dim] {marker} {BANNER_STYLE_LABELS.get(style, style)}")
        _preview_banner(BANNER_FONT, style, DISPLAY_NAME[:6])
        console.print()

    pick = console.input(f"[{col}]  Style [dim](vide = retour)[/dim] ❯ [/{col}]").strip()
    if not pick:
        return
    if not pick.isdigit() or not (1 <= int(pick) <= len(BANNER_STYLES)):
        error("Numéro invalide.")
        return
    BANNER_STYLE = BANNER_STYLES[int(pick) - 1]
    _persist_banner(f"Style : [bold]{BANNER_STYLE_LABELS[BANNER_STYLE]}[/bold]")


def rename_tool():
    col = th()["primary"]
    while True:
        t_ui = themed_table(border_style=col)
        t_ui.add_column("Réglage", style=col, width=16)
        t_ui.add_column("Valeur", style="bold white", width=40)
        t_ui.add_row("Pseudo", esc(DISPLAY_NAME))
        t_ui.add_row("Typographie", BANNER_FONT)
        t_ui.add_row("Style", BANNER_STYLE_LABELS.get(BANNER_STYLE, BANNER_STYLE))
        console.print(t_ui)

        console.print()
        console.print("  [dim]1[/dim] Changer le pseudo        [dim]2[/dim] Changer la typographie")
        console.print("  [dim]3[/dim] Changer le style couleur [dim]4[/dim] Aperçu")
        op = console.input(f"\n[{col}]  Choix [dim](vide = retour)[/dim] ❯ [/{col}]").strip()

        if op == "1":
            _change_pseudo()
        elif op == "2":
            _change_banner_font()
        elif op == "3":
            _change_banner_style()
        elif op == "4":
            console.print()
            _preview_banner(BANNER_FONT, BANNER_STYLE, DISPLAY_NAME)
        else:
            return
        console.print()

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
        # -ExecutionPolicy Bypass n'a pas lieu d'etre pour une commande inline :
        # -NonInteractive evite en plus tout blocage sur une invite cachee.
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
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
            console.print(Panel(esc(output[-2500:]), title="Journal Diskpart", border_style=th()["danger"], box=th()["box"]))
        return

    success("Opération terminée avec succès !")
    info("Appuyez sur Entrée pour revenir au menu principal.")

# ═══════════════════════════════════════════════════════
#  OUTILS TEXTE
# ═══════════════════════════════════════════════════════

def text_tools():
    col = th()["cat_uti"]
    console.print(f"\n  [{col}]Outils texte disponibles :[/{col}]")
    console.print("  [dim]1[/dim] Majuscules   [dim]2[/dim] Minuscules   [dim]3[/dim] Inverser   [dim]4[/dim] Slugify")
    console.print("  [dim]5[/dim] ROT13        [dim]6[/dim] Compteur      [dim]7[/dim] UUID       [dim]8[/dim] Capitalize")
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
    console.print("  [dim]1[/dim] Timestamp actuel   [dim]2[/dim] Timestamp → Date   [dim]3[/dim] Différence entre dates")
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
    console.print("  [dim]1[/dim] Hex → RGB   [dim]2[/dim] RGB → Hex   [dim]3[/dim] Palette")
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
    console.print("  [dim]1[/dim] URL Encode   [dim]2[/dim] URL Decode   [dim]3[/dim] HTML Entities")
    console.print("  [dim]4[/dim] Morse Encode [dim]5[/dim] Morse Decode")
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
    console.print("  [dim]1[/dim] UUID v4      [dim]2[/dim] Chaîne aléatoire   [dim]3[/dim] Hex aléatoire")
    console.print("  [dim]4[/dim] IP aléatoire [dim]5[/dim] MAC aléatoire")
    op = console.input(f"\n[{col}]  Choix ❯ [/{col}]").strip()
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Type", style=col, width=16)
    t_ui.add_column("Valeur", style="bold white", width=54)

    try:
        if op == "1":
            for _ in range(3):
                t_ui.add_row("UUID v4", str(uuid.uuid4()))
        elif op == "2":
            # `secrets` et non `random` : ces chaines servent de jetons.
            length = ask_int(col, "Longueur", 16, 1, 512)
            t_ui.add_row("Lettres+Chiffres", ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length)))
            t_ui.add_row("Lettres+Speciaux", ''.join(secrets.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(length)))
        elif op == "3":
            length = ask_int(col, "Longueur", 16, 1, 512)
            t_ui.add_row("Hex", ''.join(secrets.choice('0123456789abcdef') for _ in range(length)))
        elif op == "4":
            for _ in range(3):
                octets = [str(secrets.randbelow(256)) for _ in range(4)]
                t_ui.add_row("IPv4", '.'.join(octets))
        elif op == "5":
            for _ in range(3):
                # bit 0 du 1er octet a 0 (unicast), bit 1 a 1 (administre localement)
                first = (secrets.randbelow(256) & 0xFE) | 0x02
                rest = [secrets.randbelow(256) for _ in range(5)]
                t_ui.add_row("MAC", ':'.join('{:02x}'.format(b) for b in [first] + rest))
        else:
            error("Choix invalide.")
    except Exception as e:
        t_ui.add_row("[red]Erreur[/red]", esc(e))
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
        t_ui.add_row(str(i+1), f"[{c1}]{esc(l1[:28])}[/{c1}]", f"[{c2}]{esc(l2[:28])}[/{c2}]", status)
    console.print(t_ui)

# ═══════════════════════════════════════════════════════
#  CAPTURE ET EXPORT DES RESULTATS
# ═══════════════════════════════════════════════════════

LAST_RESULT = {"title": None, "columns": [], "rows": [], "at": None}


def _plain(cell):
    try:
        if isinstance(cell, Text):
            return cell.plain
        return Text.from_markup(str(cell)).plain
    except Exception:
        return str(cell)


class RecordingTable(Table):
    def add_column(self, header="", *args, **kwargs):
        LAST_RESULT["columns"].append(_plain(header))
        return super().add_column(header, *args, **kwargs)

    def add_row(self, *cells, **kwargs):
        LAST_RESULT["rows"].append([_plain(c) for c in cells])
        LAST_RESULT["at"] = datetime.now()
        return super().add_row(*cells, **kwargs)


def _export_rows():
    return [r for r in LAST_RESULT["rows"]
            if not all(set(c.strip()) <= set("-─ ") for c in r if c)]


def export_last_result():
    col = th()["cat_adv"]
    rows = _export_rows()
    if not rows:
        info("Aucun resultat a exporter — lance d'abord un module qui affiche un tableau.")
        return

    title = LAST_RESULT["title"] or "resultat"
    console.print(f"\n  [{col}]Dernier resultat :[/{col}] "
                  f"[bold white]{esc(title)}[/bold white] "
                  f"[dim]({len(rows)} ligne(s), {len(LAST_RESULT['columns'])} colonne(s))[/dim]")
    console.print("  [dim]1[/dim] JSON   [dim]2[/dim] CSV   [dim]3[/dim] HTML")
    fmt = console.input(f"\n[{col}]  Format ❯ [/{col}]").strip()
    if fmt not in ("1", "2", "3"):
        error("Format invalide.")
        return

    ext = {"1": "json", "2": "csv", "3": "html"}[fmt]
    slug = re.sub(r"[^A-Za-z0-9]+", "-", title.lower()).strip("-") or "resultat"
    default = f"{slug}_{datetime.now():%Y%m%d_%H%M%S}.{ext}"
    raw = console.input(f"[{col}]  Fichier [dim](default: {default})[/dim] ❯ [/{col}]").strip()
    path = os.path.abspath(os.path.expanduser(raw or default))

    cols = LAST_RESULT["columns"] or [f"col{i+1}" for i in range(len(rows[0]))]
    try:
        write_export(path, ext, title, cols, rows)
    except OSError as e:
        error(f"Ecriture impossible : {esc(e)}")
        return
    success(f"Exporte : [bold white]{esc(path)}[/bold white]")


def write_export(path, ext, title, cols, rows):
    if ext == "json":
        payload = {
            "tool": TOOL_NAME,
            "version": VERSION,
            "module": title,
            "host": platform.node(),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "columns": cols,
            "rows": [dict(zip(cols, r)) for r in rows],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

    elif ext == "csv":
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            w.writerows(rows)

    else:
        import html as html_lib
        e = html_lib.escape
        head = "".join(f"<th>{e(c)}</th>" for c in cols)
        body = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>"
                       for r in rows)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<title>{e(TOOL_NAME)} — {e(title)}</title>
<style>
 :root {{ color-scheme: dark; }}
 body {{ background:#0f1115; color:#e6e6e6; font:14px/1.5 ui-monospace,Menlo,Consolas,monospace; margin:0; padding:2rem; }}
 h1 {{ font-size:1.25rem; margin:0 0 .25rem; color:#7dd3fc; }}
 p.meta {{ color:#8b93a7; margin:0 0 1.5rem; font-size:.85rem; }}
 table {{ border-collapse:collapse; width:100%; }}
 th, td {{ text-align:left; padding:.45rem .7rem; border-bottom:1px solid #232733; }}
 th {{ color:#c4b5fd; font-weight:600; position:sticky; top:0; background:#151822; }}
 tr:hover td {{ background:#171b26; }}
</style></head><body>
<h1>{e(title)}</h1>
<p class="meta">{e(TOOL_NAME)} {e(VERSION)} &middot; {e(platform.node())} &middot;
{e(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))} &middot; {len(rows)} ligne(s)</p>
<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>
</body></html>""")


# ═══════════════════════════════════════════════════════
#  PREFERENCES ET FAVORIS
# ═══════════════════════════════════════════════════════

def _load_prefs():
    try:
        with open(PREFS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_prefs():
    return write_private_json(PREFS_PATH, {
        "theme": THEME_NAMES[CURRENT_THEME_IDX],
        "lang": LANG,
        "favorites": sorted(FAVORITES),
        "konami": KONAMI_UNLOCKED,
        "menu_anim": MENU_ANIM,
        "arcade_best": ARCADE_BEST,
    })


def preferences_menu():
    global CURRENT_THEME_IDX, LANG, MENU_ANIM
    col = th()["cat_adv"]

    anim_label = {"auto": "auto (selon le terminal)",
                  "soft": "forcee (trainee lumineuse)",
                  "off": "desactivee (menu fixe)"}

    t_ui = themed_table(border_style=col)
    t_ui.add_column("Preference", style=col, width=22)
    t_ui.add_column("Valeur", style="bold white", width=34)
    t_ui.add_row("Theme", th()["name"])
    t_ui.add_row("Langue", "Francais" if LANG == "fr" else "English")
    t_ui.add_row("Pseudo", DISPLAY_NAME)
    t_ui.add_row("Typo du pseudo", f"{BANNER_FONT} / {BANNER_STYLE}")
    t_ui.add_row("Animation du menu", anim_label.get(MENU_ANIM, MENU_ANIM))
    t_ui.add_row("Terminal detecte", esc(_terminal_label()))
    if _anim_active():
        t_ui.add_row("Animation reelle", "[green]active[/green]")
    elif MENU_ANIM == "auto":
        t_ui.add_row("Animation reelle",
                     "[yellow]coupee — ce terminal scintille[/yellow]")
    else:
        t_ui.add_row("Animation reelle", "[dim]coupee[/dim]")
    t_ui.add_row("Favoris", ", ".join(sorted(FAVORITES)) if FAVORITES else "aucun")
    if KONAMI_UNLOCKED:
        t_ui.add_row("Secret", "[bold bright_magenta]★ debloque[/bold bright_magenta]")
    t_ui.add_row("Fichier", PREFS_PATH)
    console.print(t_ui)

    console.print()
    console.print("  [dim]1[/dim] Choisir un theme        [dim]2[/dim] Ajouter un favori")
    console.print("  [dim]3[/dim] Retirer un favori       [dim]4[/dim] Tout reinitialiser")
    console.print("  [dim]5[/dim] Animation du menu       [dim]6[/dim] Pseudo & typographie")
    op = console.input(f"\n[{col}]  Choix [dim](vide = retour)[/dim] ❯ [/{col}]").strip()

    if op == "1":
        console.print()
        names = visible_theme_names()
        current = THEME_NAMES[CURRENT_THEME_IDX]
        for i, key in enumerate(names, 1):
            marker = "●" if key == current else "○"
            console.print(f"  [dim]{i}[/dim] {marker} {THEMES[key]['name']}")
        default = (names.index(current) + 1) if current in names else 1
        pick = ask_int(col, "Theme", default, 1, len(names))
        CURRENT_THEME_IDX = THEME_NAMES.index(names[pick - 1])
        success(f"Theme : [bold]{th()['name']}[/bold]")

    elif op in ("2", "3"):
        code = console.input(f"[{col}]  Numero du module [dim](ex: 08)[/dim] ❯ [/{col}]").strip().zfill(2)
        if code not in ACTIONS:
            error("Module inconnu.")
            return
        label, _ = _color_for(code)
        if op == "2":
            if len(FAVORITES) >= 12:
                error("12 favoris maximum.")
                return
            FAVORITES.add(code)
            success(f"[bold]{esc(label)}[/bold] ajoute aux favoris (★ dans le menu).")
        else:
            FAVORITES.discard(code)
            success(f"[bold]{esc(label)}[/bold] retire des favoris.")

    elif op == "4":
        if console.input(f"  [{th()['danger']}]Tapez OUI pour reinitialiser ❯ [/{th()['danger']}]").strip() != "OUI":
            info("Annule.")
            return
        FAVORITES.clear()
        CURRENT_THEME_IDX = THEME_NAMES.index("blue-magic")
        LANG = "fr"
        MENU_ANIM = "auto"
        success("Preferences reinitialisees.")

    elif op == "5":
        console.print()
        for i, mode in enumerate(MENU_ANIM_MODES, 1):
            marker = "●" if mode == MENU_ANIM else "○"
            console.print(f"  [dim]{i}[/dim] {marker} {anim_label.get(mode, mode)}")
        default = MENU_ANIM_MODES.index(MENU_ANIM) + 1
        pick = ask_int(col, "Animation", default, 1, len(MENU_ANIM_MODES))
        MENU_ANIM = MENU_ANIM_MODES[pick - 1]
        success(f"Animation : [bold]{anim_label.get(MENU_ANIM, MENU_ANIM)}[/bold]")

    elif op == "6":
        console.print()
        rename_tool()
        return

    else:
        return

    if _save_prefs():
        info(f"Sauvegarde dans {os.path.basename(PREFS_PATH)} — repris au prochain lancement.")
    else:
        warn("Sauvegarde impossible (droits sur le repertoire du script ?).")


def find_module(query):
    q = query.strip().lower()
    if not q:
        return []
    hits = []
    for _, _, items in get_cats():
        for code, label in items:
            if q in label.lower():
                hits.append((code, label))
    return hits


# ═══════════════════════════════════════════════════════
#  FICHIERS ET DONNEES
# ═══════════════════════════════════════════════════════

def _ask_dir(col, label="Repertoire", default="."):
    raw = console.input(f"[{col}]  {label} [dim](default: {default})[/dim] ❯ [/{col}]").strip()
    path = os.path.abspath(os.path.expanduser(raw or default))
    if not os.path.isdir(path):
        error(f"Repertoire introuvable : {esc(path)}")
        return None
    return path


def _walk_files(root, max_files=200000):
    seen = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirnames[:] = [d for d in dirnames
                       if not os.path.islink(os.path.join(dirpath, d))]
        for name in filenames:
            path = os.path.join(dirpath, name)
            if os.path.islink(path):
                continue
            seen += 1
            if seen > max_files:
                return
            yield path


def _human(size):
    size = float(size)
    for unit in ("o", "Ko", "Mo", "Go", "To"):
        if size < 1024 or unit == "To":
            return f"{size:.0f} {unit}" if unit == "o" else f"{size:.1f} {unit}"
        size /= 1024


def disk_usage_tree():
    col = th()["cat_sys"]
    root = _ask_dir(col, "Repertoire a analyser", os.path.expanduser("~"))
    if not root:
        return
    depth_limit = ask_int(col, "Profondeur d'agregation", 1, 1, 4)

    console.print(f"\n[dim {col}]  Analyse de {esc(root)}...[/dim {col}]")
    sizes, total, count = {}, 0, 0
    for path in _walk_files(root):
        try:
            size = os.lstat(path).st_size
        except OSError:
            continue
        total += size
        count += 1
        rel = os.path.relpath(os.path.dirname(path), root)
        key = os.sep.join(rel.split(os.sep)[:depth_limit]) if rel != "." else "."
        sizes[key] = sizes.get(key, 0) + size

    if not sizes:
        info("Aucun fichier lisible dans ce repertoire.")
        return

    LAST_RESULT["title"] = f"Espace disque — {os.path.basename(root) or root}"
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Repertoire", style="white", width=40)
    t_ui.add_column("Taille", style="bold white", width=12)
    t_ui.add_column("Part", style="dim", width=26)
    for key, size in sorted(sizes.items(), key=lambda kv: -kv[1])[:25]:
        pct = size / total * 100 if total else 0
        t_ui.add_row(esc(key[:40]), _human(size), f"{pct_bar(pct, 14)} {pct:5.1f}%")
    t_ui.add_row("─" * 38, "─" * 10, "─" * 24)
    t_ui.add_row("TOTAL", _human(total), f"{count} fichier(s)")
    console.print(t_ui)


def big_files():
    col = th()["cat_uti"]
    root = _ask_dir(col, "Repertoire a analyser", os.path.expanduser("~"))
    if not root:
        return
    top = ask_int(col, "Nombre de fichiers a lister", 20, 1, 200)
    min_mo = ask_int(col, "Taille minimale (Mo)", 1, 0, 1000000)
    threshold = min_mo * 1024 * 1024

    console.print(f"\n[dim {col}]  Recherche dans {esc(root)}...[/dim {col}]")
    found = []
    for path in _walk_files(root):
        try:
            size = os.lstat(path).st_size
        except OSError:
            continue
        if size >= threshold:
            found.append((size, path))
    found.sort(reverse=True)

    if not found:
        info(f"Aucun fichier de plus de {min_mo} Mo.")
        return

    LAST_RESULT["title"] = "Gros fichiers"
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Taille", style="bold white", width=12)
    t_ui.add_column("Modifie", style="dim", width=18)
    t_ui.add_column("Fichier", style="white", width=52)
    for size, path in found[:top]:
        try:
            mtime = datetime.fromtimestamp(os.lstat(path).st_mtime).strftime("%Y-%m-%d %H:%M")
        except OSError:
            mtime = "?"
        t_ui.add_row(_human(size), mtime, esc(path[-52:]))
    console.print(t_ui)
    info(f"{len(found)} fichier(s) au-dessus du seuil, "
         f"{_human(sum(s for s, _ in found))} au total.")


def duplicate_finder():
    col = th()["cat_uti"]
    root = _ask_dir(col, "Repertoire a analyser", ".")
    if not root:
        return
    min_ko = ask_int(col, "Ignorer les fichiers de moins de (Ko)", 1, 0, 1024000)
    threshold = min_ko * 1024

    by_size = {}
    for path in _walk_files(root):
        try:
            size = os.lstat(path).st_size
        except OSError:
            continue
        if size >= threshold and size > 0:
            by_size.setdefault(size, []).append(path)
    candidates = [paths for paths in by_size.values() if len(paths) > 1]
    if not candidates:
        success("Aucun doublon : toutes les tailles sont uniques.")
        return

    def digest(path, limit=None):
        h = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                if limit:
                    h.update(f.read(limit))
                else:
                    while chunk := f.read(1024 * 1024):
                        h.update(chunk)
        except OSError:
            return None
        return h.hexdigest()

    console.print(f"\n[dim {col}]  Comparaison de {sum(len(c) for c in candidates)} fichier(s)...[/dim {col}]")
    groups = {}
    for paths in candidates:
        prefixes = {}
        for p in paths:
            d = digest(p, 4096)
            if d:
                prefixes.setdefault(d, []).append(p)
        for same_prefix in prefixes.values():
            if len(same_prefix) < 2:
                continue
            for p in same_prefix:
                d = digest(p)
                if d:
                    groups.setdefault(d, []).append(p)

    dupes = {d: paths for d, paths in groups.items() if len(paths) > 1}
    if not dupes:
        success("Aucun doublon reel (tailles identiques mais contenus differents).")
        return

    LAST_RESULT["title"] = "Doublons"
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Groupe", style=f"dim {col}", width=8)
    t_ui.add_column("Taille", style="white", width=11)
    t_ui.add_column("Fichier", style="white", width=60)
    wasted = 0
    for i, (_, paths) in enumerate(sorted(dupes.items(), key=lambda kv: -len(kv[1])), 1):
        try:
            size = os.lstat(paths[0]).st_size
        except OSError:
            size = 0
        wasted += size * (len(paths) - 1)
        for j, p in enumerate(paths):
            t_ui.add_row(str(i) if j == 0 else "", _human(size) if j == 0 else "",
                         esc(("  " if j else "") + p[-58:]))
    console.print(t_ui)
    warn(f"{len(dupes)} groupe(s) de doublons — {_human(wasted)} recuperables.")
    info("Aucun fichier n'est supprime : la liste est fournie a titre indicatif.")


def data_converter():
    col = th()["cat_uti"]
    console.print(f"\n  [{col}]Donnees structurees :[/{col}]")
    console.print("  [dim]1[/dim] Formater / valider du JSON   [dim]2[/dim] Compacter du JSON")
    console.print("  [dim]3[/dim] JSON → CSV                   [dim]4[/dim] CSV → JSON")
    console.print("  [dim]5[/dim] JSON → YAML                  [dim]6[/dim] Analyser un fichier")
    op = console.input(f"\n[{col}]  Choix ❯ [/{col}]").strip()

    def read_input():
        src = console.input(f"[{col}]  Chemin du fichier [dim](vide = saisie directe)[/dim] ❯ [/{col}]").strip()
        if src:
            path = os.path.abspath(os.path.expanduser(src))
            if not os.path.isfile(path):
                error(f"Fichier introuvable : {esc(path)}")
                return None
            if os.path.getsize(path) > 16 * 1024 * 1024:
                error("Fichier trop volumineux (> 16 Mo).")
                return None
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        return console.input(f"[{col}]  Contenu ❯ [/{col}]")

    raw = read_input()
    if raw is None or not raw.strip():
        info("Aucune donnee.")
        return

    try:
        if op in ("1", "2", "3", "5", "6"):
            data = json.loads(raw)
    except json.JSONDecodeError as e:
        error(f"JSON invalide — ligne {e.lineno}, colonne {e.colno} : {esc(e.msg)}")
        bad = raw.splitlines()[e.lineno - 1] if 0 < e.lineno <= len(raw.splitlines()) else ""
        if bad:
            raw_print(f"    {bad[:100]}")
            raw_print("    " + " " * max(0, e.colno - 1) + "^")
        return

    if op == "1":
        success("JSON valide.")
        raw_print(json.dumps(data, indent=2, ensure_ascii=False)[:8000])

    elif op == "2":
        raw_print(json.dumps(data, separators=(",", ":"), ensure_ascii=False)[:8000])
        info(f"{len(raw)} → {len(json.dumps(data, separators=(',', ':')))} caracteres.")

    elif op == "3":
        rows = data if isinstance(data, list) else [data]
        if not all(isinstance(r, dict) for r in rows):
            error("Attendu : un objet JSON ou une liste d'objets.")
            return
        cols = list(dict.fromkeys(k for r in rows for k in r))
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})
        raw_print(buf.getvalue()[:8000])

    elif op == "4":
        rows = list(csv.DictReader(io.StringIO(raw)))
        raw_print(json.dumps(rows, indent=2, ensure_ascii=False)[:8000])
        info(f"{len(rows)} ligne(s) converties.")

    elif op == "5":
        try:
            import yaml
            raw_print(yaml.safe_dump(data, allow_unicode=True, sort_keys=False)[:8000])
        except ImportError:
            error("Le module PyYAML n'est pas installe.")
            info(f"Installe-le : {sys.executable} -m pip install pyyaml")

    elif op == "6":
        def walk(node, depth=0):
            kinds[type(node).__name__] = kinds.get(type(node).__name__, 0) + 1
            stats["max_depth"] = max(stats["max_depth"], depth)
            if isinstance(node, dict):
                for k, v in node.items():
                    keys.add(k)
                    walk(v, depth + 1)
            elif isinstance(node, list):
                for v in node:
                    walk(v, depth + 1)
        kinds, keys, stats = {}, set(), {"max_depth": 0}
        walk(data)
        LAST_RESULT["title"] = "Analyse JSON"
        t_ui = themed_table(border_style=col)
        t_ui.add_column("Metrique", style=col, width=22)
        t_ui.add_column("Valeur", style="bold white", width=44)
        t_ui.add_row("Type racine", type(data).__name__)
        t_ui.add_row("Profondeur max", str(stats["max_depth"]))
        t_ui.add_row("Cles distinctes", str(len(keys)))
        t_ui.add_row("Taille", _human(len(raw.encode("utf-8"))))
        for kind, n in sorted(kinds.items(), key=lambda kv: -kv[1]):
            t_ui.add_row(f"Noeuds {kind}", str(n))
        console.print(t_ui)
    else:
        error("Choix invalide.")


def regex_tester():
    col = th()["cat_uti"]
    pattern = console.input(f"[{col}]  Expression ❯ [/{col}]")
    if not pattern:
        return
    if len(pattern) > 500:
        error("Expression trop longue (500 caracteres maximum).")
        return
    try:
        rx = re.compile(pattern)
    except re.error as e:
        error(f"Expression invalide : {esc(e)}")
        return

    subject = console.input(f"[{col}]  Texte a tester ❯ [/{col}]")
    if len(subject) > 100000:
        error("Texte trop long (100 000 caracteres maximum).")
        return

    start = time.time()
    matches = list(rx.finditer(subject))[:200]
    elapsed = time.time() - start
    if elapsed > 1.0:
        # Un motif a retour arriere catastrophique (ex: (a+)+$) peut bloquer
        # le moteur : on ne peut pas l'interrompre, mais on avertit.
        warn(f"Motif lent ({elapsed:.2f} s) — risque de retour arriere catastrophique.")

    if not matches:
        info("Aucune correspondance.")
        return

    LAST_RESULT["title"] = "Test d'expression reguliere"
    t_ui = themed_table(border_style=col)
    t_ui.add_column("#", style=f"dim {col}", width=5)
    t_ui.add_column("Position", style="dim", width=14)
    t_ui.add_column("Correspondance", style="bold white", width=34)
    t_ui.add_column("Groupes", style="white", width=30)
    for i, m in enumerate(matches, 1):
        groups = m.groupdict() or dict(enumerate(m.groups(), 1))
        rendered = ", ".join(f"{k}={v}" for k, v in groups.items() if v is not None)
        t_ui.add_row(str(i), f"{m.start()}-{m.end()}",
                     esc(m.group(0)[:34]), esc(rendered[:30]) or "—")
    console.print(t_ui)
    success(f"{len(matches)} correspondance(s) en {elapsed * 1000:.1f} ms.")


_CRON_FIELDS = (
    ("minute", 0, 59), ("heure", 0, 23), ("jour du mois", 1, 31),
    ("mois", 1, 12), ("jour de semaine", 0, 7),
)
_CRON_ALIASES = {
    "@yearly": "0 0 1 1 *", "@annually": "0 0 1 1 *", "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0", "@daily": "0 0 * * *", "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}
_CRON_DAYS = ["dimanche", "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
_CRON_MONTHS = ["", "janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet",
                "aout", "septembre", "octobre", "novembre", "decembre"]


def _describe_cron_field(spec, name, lo, hi):
    if spec == "*":
        return f"chaque {name}"
    parts = []
    for chunk in spec.split(","):
        step = None
        if "/" in chunk:
            chunk, _, step = chunk.partition("/")
            if not step.isdigit():
                raise ValueError(f"pas invalide dans « {spec} »")
            step = int(step)
        if chunk == "*":
            parts.append(f"toutes les {step} unites" if step else f"chaque {name}")
            continue
        if "-" in chunk.lstrip("-"):
            a, _, b = chunk.partition("-")
            if not (a.isdigit() and b.isdigit()):
                raise ValueError(f"intervalle invalide : « {chunk} »")
            a, b = int(a), int(b)
            if not (lo <= a <= hi and lo <= b <= hi and a <= b):
                raise ValueError(f"intervalle hors bornes [{lo}-{hi}] : « {chunk} »")
            parts.append(f"de {a} a {b}" + (f" tous les {step}" if step else ""))
            continue
        if not chunk.isdigit():
            raise ValueError(f"valeur invalide : « {chunk} »")
        value = int(chunk)
        if not lo <= value <= hi:
            raise ValueError(f"valeur hors bornes [{lo}-{hi}] : {value}")
        if name == "jour de semaine":
            parts.append(_CRON_DAYS[value])
        elif name == "mois":
            parts.append(_CRON_MONTHS[value])
        else:
            parts.append(str(value))
    return ", ".join(parts)


def cron_explainer():
    col = th()["cat_uti"]
    console.print("\n  [dim]Exemples : «0 3 * * 1»  «*/15 * * * *»  «@daily»[/dim]")
    expr = console.input(f"[{col}]  Expression cron ❯ [/{col}]").strip()
    if not expr:
        return
    resolved = _CRON_ALIASES.get(expr.lower(), expr)
    fields = resolved.split()
    if len(fields) != 5:
        error(f"5 champs attendus, {len(fields)} recu(s) : minute heure jour mois jour-semaine.")
        return

    LAST_RESULT["title"] = "Explication cron"
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Champ", style=col, width=18)
    t_ui.add_column("Valeur", style="bold white", width=14)
    t_ui.add_column("Signification", style="white", width=44)
    descriptions = []
    valid = True
    for spec, (name, lo, hi) in zip(fields, _CRON_FIELDS):
        try:
            desc = _describe_cron_field(spec, name, lo, hi)
            descriptions.append(desc)
            t_ui.add_row(name, spec, esc(desc))
        except ValueError as e:
            valid = False
            t_ui.add_row(name, spec, f"[red]{esc(e)}[/red]")
    console.print(t_ui)

    if not valid:
        error("Expression cron invalide.")
        return
    if expr.lower() in _CRON_ALIASES:
        info(f"Alias « {esc(expr)} » = {esc(resolved)}")
    success("Execution : " + ", ".join(descriptions) + ".")


# ═══════════════════════════════════════════════════════
#  SECURITE ET RESEAU
# ═══════════════════════════════════════════════════════

def tls_inspector():
    import ssl
    col = th()["cat_net"]
    host = ask_host(col, "Domaine", "github.com")
    if not host:
        return
    port = ask_int(col, "Port", 443, 1, 65535)

    ctx = ssl.create_default_context()
    console.print(f"\n[dim {col}]  Connexion TLS a {esc(host)}:{port}...[/dim {col}]")
    verified, verify_error = True, ""
    try:
        with socket.create_connection((host, port), timeout=8) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                cert, proto, cipher = tls.getpeercert(), tls.version(), tls.cipher()
    except ssl.SSLCertVerificationError as e:
        verified, verify_error = False, str(e)
        # On rejoue sans verification uniquement pour AFFICHER le certificat
        # fautif — la connexion reste marquee comme NON approuvee.
        lax = ssl.create_default_context()
        lax.check_hostname = False
        lax.verify_mode = ssl.CERT_NONE
        try:
            with socket.create_connection((host, port), timeout=8) as sock:
                with lax.wrap_socket(sock, server_hostname=host) as tls:
                    cert, proto, cipher = tls.getpeercert(), tls.version(), tls.cipher()
        except Exception as e2:
            error(f"Connexion impossible : {esc(e2)}")
            return
    except (socket.timeout, OSError) as e:
        error(f"Connexion impossible : {esc(e)}")
        return

    def rdn(field):
        return ", ".join(v for part in (cert.get(field) or ()) for _, v in part)

    LAST_RESULT["title"] = f"Certificat TLS — {host}"
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Champ", style=col, width=22)
    t_ui.add_column("Valeur", style="white", width=56)

    if verified:
        t_ui.add_row("Verification", "[green]✔ certificat approuve[/green]")
    else:
        t_ui.add_row("Verification", "[bold red]✘ NON APPROUVE[/bold red]")
        t_ui.add_row("Motif", f"[red]{esc(verify_error[:56])}[/red]")

    t_ui.add_row("Protocole", esc(proto or "?"))
    if cipher:
        t_ui.add_row("Suite", f"{esc(cipher[0])}  [dim]{cipher[2]} bits[/dim]")
        if (proto or "") in ("TLSv1", "TLSv1.1", "SSLv3"):
            t_ui.add_row("", "[red]Protocole obsolete — a desactiver cote serveur[/red]")
    t_ui.add_row("Sujet", esc(rdn("subject")))
    t_ui.add_row("Emetteur", esc(rdn("issuer")))

    not_after = cert.get("notAfter")
    if not_after:
        try:
            expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            days = (expiry - datetime.now()).days
            if days < 0:
                state = f"[bold red]EXPIRE depuis {-days} jour(s)[/bold red]"
            elif days < 15:
                state = f"[bold red]expire dans {days} jour(s)[/bold red]"
            elif days < 30:
                state = f"[yellow]expire dans {days} jour(s)[/yellow]"
            else:
                state = f"[green]valide encore {days} jour(s)[/green]"
            t_ui.add_row("Expiration", f"{expiry:%Y-%m-%d}  {state}")
        except ValueError:
            t_ui.add_row("Expiration", esc(not_after))
    if cert.get("notBefore"):
        t_ui.add_row("Emis le", esc(cert["notBefore"]))

    sans = [v for k, v in (cert.get("subjectAltName") or ()) if k == "DNS"]
    if sans:
        t_ui.add_row("Noms alternatifs", esc(", ".join(sans[:6])
                     + (f"  (+{len(sans) - 6})" if len(sans) > 6 else "")))
    console.print(t_ui)


SECURITY_HEADERS = {
    "strict-transport-security": ("HSTS", "force HTTPS sur les visites suivantes"),
    "content-security-policy":   ("CSP", "limite les sources de scripts (anti-XSS)"),
    "x-content-type-options":    ("X-Content-Type-Options", "empeche le reniflage de type MIME"),
    "x-frame-options":           ("X-Frame-Options", "protege du clickjacking"),
    "referrer-policy":           ("Referrer-Policy", "limite la fuite d'URL au tiers"),
    "permissions-policy":        ("Permissions-Policy", "restreint camera, micro, geoloc"),
    "cross-origin-opener-policy": ("COOP", "isole le contexte de navigation"),
}
LEAKY_HEADERS = ("server", "x-powered-by", "x-aspnet-version", "x-generator")


def http_headers_audit():
    col = th()["cat_net"]
    host = ask_host(col, "Domaine", "github.com")
    if not host:
        return
    url = f"https://{host}/"
    console.print(f"\n[dim {col}]  Requete vers {esc(url)}...[/dim {col}]")

    def fetch(method):
        req = urllib.request.Request(
            url, method=method, headers={"User-Agent": f"{TOOL_NAME}/{VERSION}"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            if method == "GET":
                read_capped(resp, 256 * 1024)   # on jette le corps, borne quand meme
            return ({k.lower(): v for k, v in resp.headers.items()},
                    resp.status, resp.geturl())

    headers = status = final = None
    last_error = None
    # Beaucoup de serveurs (et de proxys) refusent HEAD : repli sur GET.
    for method in ("HEAD", "GET"):
        try:
            headers, status, final = fetch(method)
            break
        except HTTPError as e:
            last_error = e
            if e.code in (400, 403, 405, 501) and method == "HEAD":
                continue
            headers = {k.lower(): v for k, v in (e.headers or {}).items()}
            status, final = e.code, url
            break
        except Exception as e:
            last_error = e
            break
    if headers is None:
        error(f"Requete impossible : {esc(last_error)}")
        return

    LAST_RESULT["title"] = f"En-tetes de securite — {host}"
    t_ui = themed_table(border_style=col)
    t_ui.add_column("En-tete", style=col, width=26)
    t_ui.add_column("Etat", width=12)
    t_ui.add_column("Valeur / role", style="white", width=44)

    score = 0
    for key, (label, role) in SECURITY_HEADERS.items():
        value = headers.get(key)
        if value:
            score += 1
            t_ui.add_row(label, "[green]✔ present[/green]", esc(value[:44]))
        else:
            t_ui.add_row(label, "[red]✘ absent[/red]", f"[dim]{role}[/dim]")

    leaks = [(h, headers[h]) for h in LEAKY_HEADERS if h in headers]
    if leaks:
        t_ui.add_row("─" * 24, "─" * 10, "─" * 42)
        for name, value in leaks:
            t_ui.add_row(name, "[yellow]⚠ fuite[/yellow]",
                         esc(f"{value[:30]} — revele la pile technique"))
    console.print(t_ui)

    total = len(SECURITY_HEADERS)
    pct = score / total * 100
    info(f"HTTP {status} — {esc(final)}")
    console.print(f"  Score en-tetes : {pct_bar(pct, 16)} [bold]{score}/{total}[/bold]")
    if score < total:
        warn("En-tetes manquants — voir https://securityheaders.com pour le detail.")


DNS_TYPES = ("A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "CAA")
# Deux resolveurs DNS-over-HTTPS : si l'un est injoignable (reseau filtre,
# proxy d'entreprise), l'autre prend le relais. Aucune dependance ajoutee.
DOH_RESOLVERS = (
    ("dns.google", "https://dns.google/resolve"),
    ("cloudflare", "https://cloudflare-dns.com/dns-query"),
)


def _doh_query(name, rtype, timeout=6):
    headers = {"User-Agent": f"{TOOL_NAME}/{VERSION}",
               "Accept": "application/dns-json"}
    last = None
    for label, base in DOH_RESOLVERS:
        url = f"{base}?name={urllib.parse.quote(name)}&type={rtype}"
        try:
            return https_get_json(url, timeout=timeout, headers=headers), label
        except Exception as e:
            last = e
            continue
    return None, last


def dns_records():
    col = th()["cat_net"]
    host = ask_host(col, "Domaine", "github.com")
    if not host:
        return

    LAST_RESULT["title"] = f"DNS — {host}"
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Type", style=col, width=8)
    t_ui.add_column("TTL", style="dim", width=8)
    t_ui.add_column("Valeur", style="white", width=66)

    console.print(f"\n[dim {col}]  Interrogation DNS-over-HTTPS...[/dim {col}]")
    found = 0
    spf = dmarc = None
    resolver = None
    last_error = None
    for rtype in DNS_TYPES:
        data, meta = _doh_query(host, rtype)
        if data is None:
            last_error = meta
            continue
        resolver = resolver or meta
        for answer in (data.get("Answer") or [])[:8]:
            value = str(answer.get("data", "")).strip()
            t_ui.add_row(rtype, str(answer.get("TTL", "?")), esc(value[:66]))
            found += 1
            if rtype == "TXT" and "v=spf1" in value.lower():
                spf = value

    data, _ = _doh_query(f"_dmarc.{host}", "TXT")
    for answer in ((data or {}).get("Answer") or []):
        if "v=dmarc1" in str(answer.get("data", "")).lower():
            dmarc = str(answer["data"]).strip()
            t_ui.add_row("DMARC", str(answer.get("TTL", "?")), esc(dmarc[:66]))
            found += 1

    if not found:
        error("Aucun enregistrement trouve.")
        if last_error is not None:
            info(f"Resolveurs DoH injoignables ({type(last_error).__name__}) — "
                 f"reseau filtre ou proxy ? Le module 10 (Lookup DNS) fonctionne en DNS classique.")
        else:
            info("Le domaine existe-t-il ?")
        return
    console.print(t_ui)
    if resolver:
        info(f"Resolveur utilise : {resolver}")

    # Lecture de securite messagerie
    if spf:
        mode = "strict (-all)" if "-all" in spf else "souple (~all)" if "~all" in spf else "permissif"
        (success if "-all" in spf else warn)(f"SPF present — politique {mode}.")
    else:
        warn("Aucun SPF : le domaine peut etre usurpe a l'envoi de courriels.")
    if dmarc:
        policy = "none"
        m = re.search(r"p=(\w+)", dmarc)
        if m:
            policy = m.group(1)
        (success if policy in ("quarantine", "reject") else warn)(
            f"DMARC present — politique p={policy}"
            + ("" if policy in ("quarantine", "reject") else " (aucun effet reel)."))
    else:
        warn("Aucun DMARC : aucune consigne pour les courriels usurpes.")


def jwt_decoder():
    col = th()["cat_uti"]
    warn("Ce module DECODE le jeton, il ne verifie pas sa signature.")
    info("Un JWT est lisible par quiconque : ne colle jamais un jeton de production encore valide.")
    token = console.input(f"\n[{col}]  Jeton JWT ❯ [/{col}]").strip()
    if not token:
        return

    parts = token.split(".")
    if len(parts) not in (2, 3):
        error("Format invalide : un JWT compte 3 segments separes par des points.")
        return

    def b64url(segment):
        padded = segment + "=" * (-len(segment) % 4)
        return base64.urlsafe_b64decode(padded.encode())

    try:
        header = json.loads(b64url(parts[0]))
        payload = json.loads(b64url(parts[1]))
    except Exception as e:
        error(f"Decodage impossible : {esc(e)}")
        return

    LAST_RESULT["title"] = "Decodage JWT"
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Section", style=f"dim {col}", width=10)
    t_ui.add_column("Champ", style=col, width=18)
    t_ui.add_column("Valeur", style="white", width=48)

    alg = str(header.get("alg", "?"))
    for k, v in header.items():
        t_ui.add_row("header", esc(k), esc(json.dumps(v, ensure_ascii=False)[:48]))

    CLAIMS = {"iss": "emetteur", "sub": "sujet", "aud": "destinataire",
              "exp": "expiration", "nbf": "pas avant", "iat": "emis a",
              "jti": "identifiant"}
    now = time.time()
    notes = []
    for k, v in payload.items():
        rendered = json.dumps(v, ensure_ascii=False)[:48]
        if k in ("exp", "nbf", "iat") and isinstance(v, (int, float)):
            when = datetime.fromtimestamp(v).strftime("%Y-%m-%d %H:%M:%S")
            rendered = f"{int(v)}  [dim]({when})[/dim]"
        label = f"{k} [dim]{CLAIMS.get(k, '')}[/dim]" if k in CLAIMS else k
        t_ui.add_row("payload", label, rendered if k in ("exp", "nbf", "iat") else esc(rendered))
    console.print(t_ui)

    if alg.lower() == "none":
        error("alg=none : jeton non signe — accepte tel quel, c'est un contournement d'authentification.")
    elif alg.upper().startswith("HS"):
        notes.append(f"Signature symetrique ({alg}) : la cle de verification est aussi la cle de signature.")
    exp = payload.get("exp")
    if isinstance(exp, (int, float)):
        if exp < now:
            error(f"Jeton EXPIRE depuis {int((now - exp) / 60)} minute(s).")
        else:
            success(f"Jeton valide encore {int((exp - now) / 60)} minute(s).")
    else:
        warn("Aucun champ exp : ce jeton n'expire jamais.")
    if "iat" in payload and isinstance(payload["iat"], (int, float)) and payload["iat"] > now + 60:
        warn("Champ iat dans le futur.")
    for note in notes:
        info(note)

# ═══════════════════════════════════════════════════════
#  BATTERIE / ALIMENTATION
# ═══════════════════════════════════════════════════════

def battery_info():
    col = th()["cat_sys"]
    t_ui = themed_table(border_style=col)
    t_ui.add_column("", style=col, width=22)
    t_ui.add_column("", style="white", width=48)

    batt = None
    try:
        batt = psutil.sensors_battery()
    except Exception:
        pass

    if batt is None:
        t_ui.add_row("Batterie", "[dim]aucune detectee (poste fixe ?)[/dim]")
    else:
        pct = batt.percent
        t_ui.add_row("Charge", f"{pct_bar(pct)} [bold]{pct:.0f}%[/bold]")
        t_ui.add_row("Alimentation",
                     "[green]secteur branche[/green]" if batt.power_plugged
                     else "[yellow]sur batterie[/yellow]")
        secs = batt.secsleft
        if batt.power_plugged or secs == getattr(psutil, "POWER_TIME_UNLIMITED", -2):
            t_ui.add_row("Autonomie", "[dim]—[/dim]")
        elif secs is None or secs < 0:
            t_ui.add_row("Autonomie", "[dim]inconnue[/dim]")
        else:
            h, m = divmod(int(secs) // 60, 60)
            t_ui.add_row("Autonomie", f"[bold]{h}h {m:02d}m[/bold]")
        if pct < 20 and not batt.power_plugged:
            t_ui.add_row("Alerte", "[bold red]batterie faible — branche-toi[/bold red]")

    for label, fn in (("Temperatures", "sensors_temperatures"), ("Ventilateurs", "sensors_fans")):
        getter = getattr(psutil, fn, None)
        if not getter:
            continue
        try:
            data = getter() or {}
        except Exception:
            continue
        if not data:
            continue
        t_ui.add_row("─" * 20, "─" * 46)
        for name, entries in list(data.items())[:4]:
            for entry in entries[:2]:
                value = getattr(entry, "current", None)
                if value is None:
                    continue
                unit = "°C" if fn == "sensors_temperatures" else " RPM"
                t_ui.add_row(f"  {esc((entry.label or name)[:18])}", f"{value:.0f}{unit}")
    console.print(t_ui)


# ═══════════════════════════════════════════════════════
#  PASSPHRASE MEMORISABLE
# ═══════════════════════════════════════════════════════

PASSPHRASE_WORDS = (
    "arbre avion balcon banane barque bateau berger bijou biscuit blanc bleu bocal "
    "bonbon botte bougie boulon bouton branche brique brosse bulle bureau cactus cadeau "
    "cahier caillou canard canon carotte carte casque castor cerise chaise chapeau charbon "
    "chateau chemin cheval chevre chiffre cible ciseau citron clavier cloche clou cobra "
    "coffre colline colonne comete confit corde coton coude coupe courge crabe craie "
    "crayon cresson crible cuivre cygne dauphin dessin diamant domino dragon drapeau ecran "
    "ecureuil eponge epaule epice escalier etoile falaise farine fenetre ferme feuille "
    "figue filet flamme fleche fleur flocon foret fourmi fraise frere fromage fusee galet "
    "gant garage gateau girafe glacier gomme gorille goutte grange grelot grotte guitare "
    "hameau harpe hibou horloge huitre igloo image jardin jaune jeton jongleur jument "
    "kayak lampe lanterne lapin lavande lezard licorne lierre limace lingot lionne loupe "
    "lucarne lumiere lutin machine magie maison marbre marin marteau masque melon menthe "
    "meuble miel miroir moineau montagne moulin mouton muguet mursaut navire nectar neige "
    "niche nuage ocean ombre orage orange orchidee ortie oursin outil palais panda panier "
    "papier parasol pastel patin peigne pelouse perle phare piano pierre pigeon pilote "
    "pinceau pirate piste plage planche plume poivre pomme pont portail poterie poulain "
    "prairie prisme prune puzzle pyramide quartz radeau raisin rameau rapide renard requin "
    "rideau rivage rocher rosier rubis ruche sabot safran sapin sardine sauge savon scarabee "
    "sculpture semelle sentier serpent silex sirene soleil sommet sorbet source souris "
    "sucre table tambour tapis taupe temple tigre tissu toile tomate torche tortue toupie "
    "tournesol trefle tresor tribu tulipe tunnel vague vallee vanille velours verger vernis "
    "violon voile volcan yaourt zebre zenith"
).split()


def passphrase_gen():
    import math
    col = th()["cat_uti"]
    if not sensitive_notice("phrases de passe générées en clair"):
        return
    words = ask_int(col, "Nombre de mots", 8, 3, 16)
    sep_raw = console.input(f"[{col}]  Separateur [dim](default: -)[/dim] ❯ [/{col}]").strip()
    sep = sep_raw[:3] or "-"

    pool = len(PASSPHRASE_WORDS)
    entropy = words * math.log2(pool)

    t_ui = themed_table(border_style=col)
    t_ui.add_column("#", style=f"dim {col}", width=4)
    t_ui.add_column("Phrase de passe", style="bold white", width=56)
    t_ui.add_column("Longueur", style="dim", width=12)

    for i in range(5):
        picked = [secrets.choice(PASSPHRASE_WORDS) for _ in range(words)]
        # Un mot capitalise et un chiffre : accepte par la plupart des politiques
        # de mot de passe, sans nuire a la memorisation.
        idx = secrets.randbelow(words)
        picked[idx] = picked[idx].capitalize()
        phrase = sep.join(picked) + sep + str(secrets.randbelow(100))
        t_ui.add_row(str(i + 1), phrase, f"{len(phrase)} car.")
    console.print(t_ui)

    info(f"Tire dans {pool} mots avec `secrets` — entropie ~{entropy:.0f} bits "
         f"(hors capitale et chiffre ajoutes).")
    crack = (2 ** entropy) / 1e10 / 2
    info(f"Temps de cassage estime hors ligne (10^10 tentatives/s) : {_human_duration(crack)}")

    if entropy < 50:
        error(f"Entropie faible ({entropy:.0f} bits) — ajoute des mots "
              f"(8 minimum recommande avec cette liste).")
    elif entropy < 70:
        warn(f"Entropie moyenne ({entropy:.0f} bits) — convient a un usage courant, "
             f"pas a un secret critique.")
    else:
        success(f"Entropie solide ({entropy:.0f} bits).")


# ═══════════════════════════════════════════════════════
#  INTEGRITE DES FICHIERS
# ═══════════════════════════════════════════════════════

INTEGRITY_MAX_FILES = 20000
INTEGRITY_MAX_FILE_BYTES = 100 * 1024 * 1024


def _baseline_path(root):
    slug = hashlib.sha256(os.path.abspath(root).encode("utf-8")).hexdigest()[:16]
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        f".{TOOL_NAME}_baseline_{slug}.json")


def _hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(262144)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _scan_integrity(root):
    snapshot, skipped = {}, 0
    for path in _walk_files(root, max_files=INTEGRITY_MAX_FILES):
        try:
            size = os.lstat(path).st_size
            if size > INTEGRITY_MAX_FILE_BYTES:
                skipped += 1
                continue
            snapshot[os.path.relpath(path, root)] = {
                "sha256": _hash_file(path),
                "size": size,
            }
        except (OSError, PermissionError):
            skipped += 1
    return snapshot, skipped


def file_integrity():
    col = th()["cat_sys"]
    root = _ask_dir(col, "Repertoire a surveiller", ".")
    if not root:
        return
    store = _baseline_path(root)
    has_baseline = os.path.exists(store)

    console.print()
    console.print(f"  [dim]1[/dim] Enregistrer l'empreinte de reference"
                  f"{'  [dim](ecrase l existante)[/dim]' if has_baseline else ''}")
    console.print(f"  [dim]2[/dim] Comparer avec l'empreinte de reference"
                  f"{'' if has_baseline else '  [dim](aucune enregistree)[/dim]'}")
    op = console.input(f"\n[{col}]  Choix ❯ [/{col}]").strip()

    if op == "1":
        console.print(f"\n[dim {col}]  Analyse de {esc(root)}...[/dim {col}]")
        snapshot, skipped = _scan_integrity(root)
        if not snapshot:
            error("Aucun fichier lisible dans ce repertoire.")
            return
        ok = write_private_json(store, {
            "root": os.path.abspath(root),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "files": snapshot,
        })
        if not ok:
            error("Ecriture de l'empreinte impossible.")
            return
        success(f"Empreinte enregistree : {len(snapshot)} fichier(s).")
        if skipped:
            warn(f"{skipped} fichier(s) ignore(s) (illisibles ou > 100 Mo).")
        info(f"Fichier : {os.path.basename(store)}")
        return

    if op != "2":
        return
    if not has_baseline:
        error("Aucune empreinte de reference — lance d'abord l'option 1.")
        return

    try:
        with open(store, "r", encoding="utf-8") as f:
            data = json.load(f)
        old = data.get("files") or {}
    except Exception as e:
        error(f"Empreinte illisible : {esc(e)}")
        return

    console.print(f"\n[dim {col}]  Comparaison de {esc(root)}...[/dim {col}]")
    new, skipped = _scan_integrity(root)

    added    = sorted(set(new) - set(old))
    removed  = sorted(set(old) - set(new))
    modified = sorted(p for p in set(old) & set(new)
                      if old[p].get("sha256") != new[p]["sha256"])

    LAST_RESULT["title"] = f"Integrite — {os.path.basename(root) or root}"
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Etat", width=14)
    t_ui.add_column("Fichier", style="white", width=54)
    t_ui.add_column("Taille", style="dim", width=12)

    for path in modified[:60]:
        t_ui.add_row("[bold red]MODIFIE[/bold red]", esc(path[:54]), _human(new[path]["size"]))
    for path in added[:60]:
        t_ui.add_row("[yellow]AJOUTE[/yellow]", esc(path[:54]), _human(new[path]["size"]))
    for path in removed[:60]:
        t_ui.add_row("[bright_black]SUPPRIME[/bright_black]", esc(path[:54]),
                     _human(old[path].get("size", 0)))
    if not (modified or added or removed):
        t_ui.add_row("[green]INTACT[/green]", "aucun changement detecte", "—")
    console.print(t_ui)

    info(f"Reference du {esc(data.get('created_at', '?'))} — {len(old)} fichier(s).")
    console.print(f"  [bold red]{len(modified)} modifie(s)[/bold red]   "
                  f"[yellow]{len(added)} ajoute(s)[/yellow]   "
                  f"[bright_black]{len(removed)} supprime(s)[/bright_black]")
    if skipped:
        warn(f"{skipped} fichier(s) ignore(s) (illisibles ou > 100 Mo).")


# ═══════════════════════════════════════════════════════
#  BENCHMARK RAPIDE
# ═══════════════════════════════════════════════════════

def benchmark():
    col = th()["cat_sys"]
    info("Test court (~6 s). Ferme les applications lourdes pour un resultat fiable.")
    console.print()

    t_ui = themed_table(border_style=col)
    t_ui.add_column("Test", style=col, width=20)
    t_ui.add_column("Resultat", style="bold white", width=24)
    t_ui.add_column("Detail", style="dim", width=34)

    # CPU : hachage en boucle pendant une duree fixe.
    block = secrets.token_bytes(65536)
    rounds, start, deadline = 0, time.perf_counter(), time.perf_counter() + 2.0
    while time.perf_counter() < deadline:
        hashlib.sha256(block).digest()
        rounds += 1
    cpu_elapsed = time.perf_counter() - start
    cpu_mbs = rounds * len(block) / cpu_elapsed / 1e6
    t_ui.add_row("CPU (SHA-256)", f"{cpu_mbs:.0f} Mo/s", f"{rounds} blocs de 64 Ko en {cpu_elapsed:.1f}s")

    # Memoire : copie de tampon.
    buf = bytearray(32 * 1024 * 1024)
    start = time.perf_counter()
    copies = 0
    while time.perf_counter() - start < 1.5:
        buf[:] = buf
        copies += 1
    mem_elapsed = time.perf_counter() - start
    mem_mbs = copies * len(buf) / mem_elapsed / 1e6
    t_ui.add_row("Memoire (copie)", f"{mem_mbs:.0f} Mo/s", f"{copies} copies de 32 Mo")
    del buf

    # Disque : ecriture puis lecture d'un fichier temporaire.
    payload = secrets.token_bytes(1024 * 1024) * 32   # 32 Mo
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(prefix=f"{TOOL_NAME}_bench_")
        start = time.perf_counter()
        with os.fdopen(fd, "wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        write_s = time.perf_counter() - start
        start = time.perf_counter()
        with open(tmp_path, "rb") as f:
            while f.read(1024 * 1024):
                pass
        read_s = time.perf_counter() - start
        t_ui.add_row("Disque (ecriture)", f"{len(payload) / write_s / 1e6:.0f} Mo/s",
                     f"32 Mo en {write_s:.2f}s (avec fsync)")
        t_ui.add_row("Disque (lecture)", f"{len(payload) / read_s / 1e6:.0f} Mo/s",
                     f"32 Mo en {read_s:.2f}s (cache possible)")
    except OSError as e:
        t_ui.add_row("Disque", "[red]echec[/red]", esc(str(e)[:34]))
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    t_ui.add_row("─" * 18, "─" * 22, "─" * 32)
    t_ui.add_row("Machine", esc(platform.node()),
                 f"{psutil.cpu_count(logical=True)} threads")
    console.print(t_ui)


# ═══════════════════════════════════════════════════════
#  PORTS EN ECOUTE
# ═══════════════════════════════════════════════════════

RISKY_LISTEN_PORTS = {
    21: "FTP (clair)", 23: "Telnet (clair)", 445: "SMB", 3389: "RDP",
    5900: "VNC", 3306: "MySQL", 5432: "PostgreSQL", 27017: "MongoDB",
    6379: "Redis", 9200: "Elasticsearch", 11211: "Memcached",
}


def listening_ports():
    col = th()["cat_net"]
    if not sensitive_notice("services en écoute sur cette machine"):
        return
    try:
        conns = psutil.net_connections(kind="inet")
    except (psutil.AccessDenied, PermissionError):
        error("Droits insuffisants — relance en root/administrateur.")
        return

    listening = [c for c in conns if c.status == psutil.CONN_LISTEN]
    if not listening:
        info("Aucun service en ecoute detecte.")
        return

    LAST_RESULT["title"] = "Ports en ecoute"
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Proto", style=col, width=8)
    t_ui.add_column("Adresse", style="white", width=26)
    t_ui.add_column("Port", style="bold white", width=8)
    t_ui.add_column("Processus", style="dim", width=22)
    t_ui.add_column("Exposition", width=26)

    exposed = 0
    seen = set()
    for c in sorted(listening, key=lambda c: (getattr(c.laddr, "port", 0))):
        ip   = getattr(c.laddr, "ip", "?")
        port = getattr(c.laddr, "port", 0)
        key  = (ip, port, c.pid)
        if key in seen:
            continue
        seen.add(key)

        name = "?"
        if c.pid:
            try:
                name = psutil.Process(c.pid).name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        public = ip in ("0.0.0.0", "::", "")
        if public:
            exposed += 1
            risk = RISKY_LISTEN_PORTS.get(port)
            note = (f"[bold red]toutes interfaces — {risk}[/bold red]" if risk
                    else "[yellow]toutes interfaces[/yellow]")
        else:
            note = "[green]local uniquement[/green]"

        proto = "TCP" if c.type == socket.SOCK_STREAM else "UDP"
        t_ui.add_row(proto, esc(str(ip)), str(port),
                     esc(f"{name}({c.pid})" if c.pid else name), note)
    console.print(t_ui)

    info(f"{len(seen)} service(s) en ecoute, dont {exposed} accessible(s) depuis le reseau.")
    if exposed:
        warn("Un service en ecoute sur 0.0.0.0 est joignable par toute machine du reseau.")


# ═══════════════════════════════════════════════════════
#  BILAN DE SANTE
# ═══════════════════════════════════════════════════════
# Chaque controle rend (etiquette, mesure, verdict, poids, conseil). Le verdict
# vaut 0 (bon), 1 (a surveiller) ou 2 (probleme) ; le score final est la part
# des points perdus sur le total des poids, ce qui evite qu'un seul controle
# secondaire fasse chuter la note.
HEALTH_OK, HEALTH_WARN, HEALTH_BAD = 0, 1, 2
HEALTH_VERDICTS = {
    HEALTH_OK:   ("[green]✔ bon[/green]", "green"),
    HEALTH_WARN: ("[yellow]⚠ a surveiller[/yellow]", "yellow"),
    HEALTH_BAD:  ("[bold red]✘ probleme[/bold red]", "red"),
}


def _health_cpu():
    load = psutil.cpu_percent(interval=0.4)
    verdict = HEALTH_OK if load < 70 else HEALTH_WARN if load < 90 else HEALTH_BAD
    return ("Charge CPU", f"{load:.0f}%", verdict, 3,
            "souvent un processus emballe — voir le module 14.")


def _health_ram():
    vm = psutil.virtual_memory()
    verdict = HEALTH_OK if vm.percent < 75 else HEALTH_WARN if vm.percent < 90 else HEALTH_BAD
    return ("Memoire vive", f"{vm.percent:.0f}% de {_human(vm.total)}", verdict, 3,
            "la machine va swapper et ramer — ferme des applications.")


def _health_swap():
    try:
        sw = psutil.swap_memory()
    except Exception:
        return None
    if not sw.total:
        return None
    verdict = HEALTH_OK if sw.percent < 40 else HEALTH_WARN if sw.percent < 75 else HEALTH_BAD
    return ("Fichier d'echange", f"{sw.percent:.0f}% de {_human(sw.total)}", verdict, 1,
            "swap tres sollicite : il manque de la RAM physique.")


def _health_disks():
    rows = []
    for part in psutil.disk_partitions(all=False):
        if "cdrom" in (part.opts or "") or not part.fstype:
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        verdict = (HEALTH_OK if usage.percent < 80
                   else HEALTH_WARN if usage.percent < 92 else HEALTH_BAD)
        rows.append((f"Disque {part.mountpoint}",
                     f"{usage.percent:.0f}% — {_human(usage.free)} libres",
                     verdict, 3,
                     "presque plein — modules 19 (temp) et 49 (gros fichiers)."))
    return rows


def _health_uptime():
    up = (datetime.now() - datetime.fromtimestamp(psutil.boot_time())).total_seconds()
    days = up / 86400
    verdict = HEALTH_OK if days < 7 else HEALTH_WARN if days < 30 else HEALTH_BAD
    return ("Uptime", _human_duration(up), verdict, 1,
            "redemarre pour appliquer les mises a jour de securite.")


def _health_battery():
    getter = getattr(psutil, "sensors_battery", None)
    if not getter:
        return None
    try:
        batt = getter()
    except Exception:
        return None
    if batt is None:
        return None
    pct = batt.percent
    if batt.power_plugged:
        verdict = HEALTH_OK
    else:
        verdict = HEALTH_OK if pct > 40 else HEALTH_WARN if pct > 15 else HEALTH_BAD
    state = "secteur" if batt.power_plugged else "sur batterie"
    return ("Batterie", f"{pct:.0f}% ({state})", verdict, 1,
            "batterie basse sans secteur — branche-toi.")


def _health_temperature():
    getter = getattr(psutil, "sensors_temperatures", None)
    if not getter:
        return None
    try:
        data = getter() or {}
    except Exception:
        return None
    peaks = [getattr(e, "current", None) for entries in data.values() for e in entries]
    peaks = [p for p in peaks if isinstance(p, (int, float)) and p > 0]
    if not peaks:
        return None
    hottest = max(peaks)
    verdict = HEALTH_OK if hottest < 75 else HEALTH_WARN if hottest < 90 else HEALTH_BAD
    return ("Temperature max", f"{hottest:.0f} °C", verdict, 2,
            "ca chauffe — verifie ventilation et poussiere.")


def _health_processes():
    count = len(psutil.pids())
    verdict = HEALTH_OK if count < 350 else HEALTH_WARN if count < 600 else HEALTH_BAD
    return ("Processus actifs", str(count), verdict, 1,
            "beaucoup de processus — voir le module 14.")


def _health_exposure():
    try:
        conns = psutil.net_connections(kind="inet")
    except (psutil.AccessDenied, PermissionError):
        return ("Ports exposes", "[dim]droits insuffisants[/dim]", HEALTH_OK, 0,
                "Relance en administrateur pour auditer les ports en ecoute.")
    except Exception:
        return None

    exposed, risky = set(), []
    for c in conns:
        if c.status != psutil.CONN_LISTEN:
            continue
        ip = getattr(c.laddr, "ip", "")
        port = getattr(c.laddr, "port", 0)
        if ip in ("0.0.0.0", "::", ""):
            exposed.add(port)
            if port in RISKY_LISTEN_PORTS:
                risky.append(port)

    if risky:
        verdict, detail = HEALTH_BAD, f"{len(exposed)} dont {len(set(risky))} sensible(s)"
    elif len(exposed) > 8:
        verdict, detail = HEALTH_WARN, f"{len(exposed)} sur toutes interfaces"
    else:
        verdict, detail = HEALTH_OK, f"{len(exposed)} sur toutes interfaces"
    return ("Ports exposes", detail, verdict, 2,
            "services joignables du reseau — detail au module 64.")


def _health_temp_dir():
    total = 0
    files = 0
    root = tempfile.gettempdir()
    try:
        with os.scandir(root) as it:
            for entry in it:
                files += 1
                if files > 4000:
                    break
                try:
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size
                except OSError:
                    continue
    except OSError:
        return None
    mo = total / 1048576
    verdict = HEALTH_OK if mo < 500 else HEALTH_WARN if mo < 2048 else HEALTH_BAD
    return ("Dossier temporaire", f"{_human(total)} ({files} entrees)", verdict, 1,
            "temporaire encombre — le module 19 le nettoie.")


def health_check():
    col = th()["cat_mon"]
    console.print(f"[dim {col}]  Analyse de la machine en cours...[/dim {col}]\n")

    checks = []
    for probe in (_health_cpu, _health_ram, _health_swap, _health_disks,
                  _health_temperature, _health_battery, _health_uptime,
                  _health_processes, _health_exposure, _health_temp_dir):
        try:
            result = probe()
        except Exception:
            # Un capteur indisponible ne doit pas interrompre le bilan.
            continue
        if not result:
            continue
        checks.extend(result if isinstance(result, list) else [result])

    if not checks:
        error("Aucun indicateur n'a pu etre mesure sur cette machine.")
        return

    LAST_RESULT["title"] = "Bilan de sante"
    t_ui = themed_table(border_style=col)
    t_ui.add_column("Controle", style=col, width=22)
    t_ui.add_column("Mesure", style="bold white", width=32)
    t_ui.add_column("Verdict", width=18)

    lost = weight_total = 0
    advice = []
    for label, measure, verdict, weight, tip in checks:
        t_ui.add_row(label, measure, HEALTH_VERDICTS[verdict][0])
        weight_total += weight
        lost += weight * verdict
        if verdict != HEALTH_OK and weight:
            advice.append((verdict, label, tip))
    console.print(t_ui)

    # Un verdict « probleme » coute deux fois un « a surveiller », d'ou le
    # denominateur double du total des poids.
    score = 100 - int(round(lost / max(1, weight_total * 2) * 100))
    grade, gcol = (("EXCELLENT", "bright_green") if score >= 90 else
                   ("BON", "green") if score >= 75 else
                   ("MOYEN", "yellow") if score >= 55 else
                   ("FRAGILE", "bright_red"))

    console.print()
    console.print(f"  Sante globale  {pct_bar(score, 24, theme_colors=False)} "
                  f"[bold {gcol}]{score}/100 — {grade}[/bold {gcol}]")

    ok_count = sum(1 for c in checks if c[2] == HEALTH_OK)
    info(f"{ok_count}/{len(checks)} controles au vert.")

    if not advice:
        success("Rien a signaler — la machine est en bonne forme.")
        return

    console.print()
    console.print(f"  [{col}]Recommandations[/{col}]")
    for verdict, label, tip in sorted(advice, key=lambda a: -a[0])[:6]:
        bullet = "[bold red]![/bold red]" if verdict == HEALTH_BAD else "[yellow]·[/yellow]"
        console.print(f"   {bullet} [bold]{esc(label)}[/bold] — {esc(tip)}")


# ═══════════════════════════════════════════════════════
#  SECRET
# ═══════════════════════════════════════════════════════

def _konami_animation():
    if not sys.stdin.isatty():
        return
    symbols = ["▲", "▲", "▼", "▼", "◄", "►", "◄", "►", "B", "A"]
    colors  = ["bright_magenta", "bright_yellow", "bright_cyan", "bright_green"]
    try:
        with Live(Text(""), console=console, refresh_per_second=30, transient=True) as live:
            for step in range(len(symbols) + 3):
                line = Text()
                for i, sym in enumerate(symbols):
                    if i < step:
                        line.append(f" {sym} ", style=f"bold {colors[i % len(colors)]}")
                    else:
                        line.append(f" {sym} ", style="bright_black")
                live.update(Align.center(line))
                time.sleep(0.07)
    except Exception:
        pass


def konami_unlock():
    global KONAMI_UNLOCKED, CURRENT_THEME_IDX
    already = KONAMI_UNLOCKED
    _konami_animation()

    body = Text()
    body.append("↑ ↑ ↓ ↓ ← → ← → B A\n\n", style="bold bright_yellow")
    if already:
        body.append("Secret déjà débloqué.\n", style="bright_white")
        body.append("Thème Arcade ★ et module 99 disponibles.", style="bright_cyan")
    else:
        body.append("SECRET DÉBLOQUÉ\n", style="bold bright_green")
        body.append("Thème  ", style="bright_white")
        body.append("Arcade ★", style="bold bright_magenta")
        body.append("  ·  Module  ", style="bright_white")
        body.append("99 Mode Arcade", style="bold bright_cyan")
    console.print(Align.center(Panel(
        body, border_style="bright_magenta", box=box.DOUBLE_EDGE,
        padding=(1, 6), title="[bold bright_yellow]★ KONAMI ★[/bold bright_yellow]",
    )))

    if not already:
        KONAMI_UNLOCKED = True
        CURRENT_THEME_IDX = THEME_NAMES.index("arcade")
        if _save_prefs():
            info("Débloqué définitivement — repris au prochain lancement.")
        else:
            warn("Déblocage actif pour cette session (sauvegarde impossible).")
        info("Thème Arcade appliqué — module 27 pour en changer.")


class _KeyReader:
    """Lit le clavier touche par touche, sans attendre la touche Entree.

    Les fleches arrivent en deux morceaux (prefixe puis code sous Windows,
    sequence ESC ailleurs) : elles sont traduites en jetons <UP>/<DOWN>/... comme
    dans le menu, pour que le jeu n'ait pas a s'en soucier.
    """

    def __init__(self):
        self._saved = None
        self._fd = None

    def __enter__(self):
        if os.name != "nt":
            import termios
            import tty
            self._fd = sys.stdin.fileno()
            self._saved = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
        return self

    def __exit__(self, *exc):
        if self._saved is not None:
            import termios
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._saved)
        return False

    def read(self) -> str:
        if os.name == "nt":
            import msvcrt
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):
                return _WIN_ARROWS.get(msvcrt.getwch(), "")
            return ch

        import select
        ch = sys.stdin.read(1)
        if ch != "\x1b":
            return ch
        seq = ""
        for _ in range(2):
            ready, _, _ = select.select([sys.stdin], [], [], 0.05)
            if not ready:
                break
            seq += sys.stdin.read(1)
        if len(seq) == 2 and seq[0] in ("[", "O"):
            return _UNIX_ARROWS.get(seq[1], "")
        return "\x1b"


# ── 2048 ──────────────────────────────────────────────────
TILE_STYLES = {
    0: "bright_black", 2: "white", 4: "bright_white", 8: "yellow",
    16: "bright_yellow", 32: "orange1", 64: "bright_red",
    128: "magenta", 256: "bright_magenta", 512: "cyan",
    1024: "bright_cyan", 2048: "bright_green",
}


def _g2048_new():
    grid = [[0] * 4 for _ in range(4)]
    _g2048_spawn(grid)
    _g2048_spawn(grid)
    return grid


def _g2048_spawn(grid) -> bool:
    empty = [(r, c) for r in range(4) for c in range(4) if grid[r][c] == 0]
    if not empty:
        return False
    r, c = secrets.choice(empty)
    grid[r][c] = 4 if secrets.randbelow(10) == 0 else 2
    return True


def _g2048_slide(row):
    """Compacte une ligne vers la gauche et fusionne les paires egales."""
    tiles = [v for v in row if v]
    out, gained, i = [], 0, 0
    while i < len(tiles):
        if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
            merged = tiles[i] * 2
            out.append(merged)
            gained += merged
            i += 2
        else:
            out.append(tiles[i])
            i += 1
    out += [0] * (4 - len(out))
    return out, gained


def _g2048_move(grid, direction):
    """Joue un coup. Retourne (nouvelle grille, points, la grille a bouge)."""
    rows = [list(r) for r in grid]
    if direction in ("<UP>", "<DOWN>"):
        rows = [list(col) for col in zip(*rows)]          # travaille en colonnes
    reverse = direction in ("<RIGHT>", "<DOWN>")

    gained = 0
    for i, row in enumerate(rows):
        line = row[::-1] if reverse else row
        line, points = _g2048_slide(line)
        rows[i] = line[::-1] if reverse else line
        gained += points

    if direction in ("<UP>", "<DOWN>"):
        rows = [list(col) for col in zip(*rows)]
    return rows, gained, rows != [list(r) for r in grid]


def _g2048_can_move(grid) -> bool:
    for r in range(4):
        for c in range(4):
            if grid[r][c] == 0:
                return True
            if c < 3 and grid[r][c] == grid[r][c + 1]:
                return True
            if r < 3 and grid[r][c] == grid[r + 1][c]:
                return True
    return False


def _g2048_render(grid, score, best, message=""):
    col = th()["cat_adv"]
    table = Table(box=_menu_box(), border_style=col, show_header=False,
                  padding=(0, 1))
    for _ in range(4):
        table.add_column(width=7, justify="center")
    for row in grid:
        cells = []
        for value in row:
            if value == 0:
                cells.append(Text("·", style="bright_black"))
            else:
                style = TILE_STYLES.get(value, "bright_green")
                cells.append(Text(str(value), style=f"bold {style}"))
        table.add_row(*cells)

    header = Text.assemble(
        ("SCORE ", th()["dim_col"]), (f"{score}", f"bold {th()['accent']}"),
        ("     RECORD ", th()["dim_col"]), (f"{best}", f"bold {th()['success']}"),
    )
    footer = Text("fleches pour jouer · r pour recommencer · q pour quitter",
                  style=th()["dim_col"])

    parts = [Align.center(header), Text(""), Align.center(table)]
    if message:
        parts += [Text(""), Align.center(message)]
    parts += [Text(""), Align.center(footer)]
    return Group(*parts)


def _game_2048():
    global ARCADE_BEST
    if HEADLESS or not sys.stdin.isatty():
        info("Le jeu demande un vrai terminal.")
        return

    grid = _g2048_new()
    score, message = 0, ""
    won = False

    with _KeyReader() as keys:
        while True:
            clr()
            console.print()
            console.print(Align.center(Text("2 0 4 8", style=f"bold {th()['accent']}")))
            console.print()
            console.print(_g2048_render(grid, score, ARCADE_BEST, message))

            key = keys.read()
            if key in ("q", "Q", "\x1b", "\x03"):
                break
            if key in ("r", "R"):
                grid, score, message, won = _g2048_new(), 0, "", False
                continue
            if key not in ("<UP>", "<DOWN>", "<LEFT>", "<RIGHT>"):
                continue

            grid, gained, moved = _g2048_move(grid, key)
            if not moved:
                message = Text("bloque de ce cote", style=th()["warning"])
                continue

            score += gained
            if score > ARCADE_BEST:
                ARCADE_BEST = score
                _save_prefs()

            _g2048_spawn(grid)
            message = ""

            if not won and any(v >= 2048 for row in grid for v in row):
                won = True
                message = Text("2048 ! continue si tu veux",
                               style=f"bold {th()['success']}")
            if not _g2048_can_move(grid):
                clr()
                console.print()
                console.print(_g2048_render(
                    grid, score, ARCADE_BEST,
                    Text("PARTIE TERMINEE", style=f"bold {th()['danger']}")))
                console.print()
                if console.input("  Rejouer ? [dim][O/n][/dim] ❯ ").strip().lower() in ("", "o", "oui", "y"):
                    grid, score, message, won = _g2048_new(), 0, "", False
                else:
                    break

    console.print()
    success(f"Score final : [bold]{score}[/bold] — record : [bold]{ARCADE_BEST}[/bold]")


def arcade_mode():
    col = "bright_magenta"
    logo = None
    for font in ("small", "mini", "standard"):
        try:
            candidate = pyfiglet.figlet_format("ARCADE", font=font, width=_screen_width())
        except Exception:
            continue
        logo = candidate
        break
    if logo:
        palette = ["bright_magenta", "bright_yellow", "bright_cyan", "bright_green"]
        for i, line in enumerate(logo.rstrip().splitlines()):
            console.print(Align.center(Text(line, style=f"bold {palette[i % len(palette)]}")))
    console.print()

    boot = datetime.fromtimestamp(psutil.boot_time())
    up_h = (datetime.now() - boot).total_seconds() / 3600
    vm = psutil.virtual_memory()
    procs = len(psutil.pids())
    modules = sum(1 for _, _, items in get_cats() for code, _ in items if code != "00")
    score = int(up_h * 100 + procs * 7 + (100 - vm.percent) * 13)

    t_ui = themed_table(border_style=col)
    t_ui.add_column("", style=col, width=20)
    t_ui.add_column("", style="bold white", width=44)
    t_ui.add_row("PLAYER", esc(DISPLAY_NAME))
    t_ui.add_row("MACHINE", esc(f"{getpass.getuser()}@{platform.node()}"))
    t_ui.add_row("HIGH SCORE", f"[bold bright_yellow]{score:,}[/bold bright_yellow]".replace(",", " "))
    t_ui.add_row("STAGE", f"{up_h:.1f} h d'uptime")
    t_ui.add_row("MODULES", f"{modules} debloques")
    t_ui.add_row("FAVORIS", str(len(FAVORITES)))
    t_ui.add_row("THEME", th()["name"])
    t_ui.add_row("RECORD 2048", f"[bold bright_green]{ARCADE_BEST}[/bold bright_green]"
                 if ARCADE_BEST else "[dim]jamais joue[/dim]")
    t_ui.add_row("CREDITS", f"{TOOL_NAME} {VERSION}")
    console.print(t_ui)
    console.print()
    console.print(Align.center(Text("★  INSERT COIN  ★", style="bold bright_yellow")))
    console.print()

    if HEADLESS or not sys.stdin.isatty():
        return
    choice = console.input(
        f"  [{col}]Jouer a 2048 ? [dim][O/n][/dim] ❯ [/{col}]"
    ).strip().lower()
    if choice in ("", "o", "oui", "y", "yes"):
        _game_2048()


# ── Application des preferences enregistrees ─────────────
_PREFS = _load_prefs()
KONAMI_UNLOCKED = bool(_PREFS.get("konami"))
if _PREFS.get("theme") in THEME_NAMES:
    # Un theme secret enregistre ne se recharge que s'il est encore debloque.
    if _PREFS["theme"] not in HIDDEN_THEMES or KONAMI_UNLOCKED:
        CURRENT_THEME_IDX = THEME_NAMES.index(_PREFS["theme"])
if _PREFS.get("lang") in ("fr", "en"):
    LANG = _PREFS["lang"]
if _PREFS.get("menu_anim") in MENU_ANIM_MODES:
    MENU_ANIM = _PREFS["menu_anim"]
try:
    ARCADE_BEST = max(0, int(_PREFS.get("arcade_best") or 0))
except (TypeError, ValueError):
    ARCADE_BEST = 0
FAVORITES.update(str(c).zfill(2) for c in (_PREFS.get("favorites") or [])[:12])


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
    "48": disk_usage_tree,
    "49": big_files,
    "50": duplicate_finder,
    "51": data_converter,
    "52": regex_tester,
    "53": cron_explainer,
    "54": export_last_result,
    "55": tls_inspector,
    "56": http_headers_audit,
    "57": dns_records,
    "58": jwt_decoder,
    "59": preferences_menu,
    "60": battery_info,
    "61": passphrase_gen,
    "62": file_integrity,
    "63": benchmark,
    "64": listening_ports,
    "65": health_check,
    "99": arcade_mode,
}

# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════
def _run_action(fn, choice):
    label, _ = _color_for(choice)
    LAST_RESULT["title"] = label if label != choice else fn.__name__
    try:
        fn()
        return True
    except KeyboardInterrupt:
        console.print()
        info("Interrompu — retour au menu.")
        return True
    except PermissionError as e:
        error(f"Droits insuffisants : {esc(e)}")
        info("Relance l'outil en administrateur / root pour ce module.")
    except FileNotFoundError as e:
        error(f"Commande ou fichier introuvable : {esc(e)}")
    except (URLError, HTTPError, socket.error, TimeoutError) as e:
        error(f"Erreur reseau : {esc(e)}")
    except subprocess.TimeoutExpired:
        error("La commande a depasse le delai imparti.")
    except Exception as e:
        error(f"Erreur inattendue dans le module {esc(choice)} : {type(e).__name__} — {esc(e)}")
        if DEBUG:
            raw_print(traceback.format_exc())
        else:
            info("Relance avec WEAK_TOOL_DEBUG=1 pour la trace complete.")
    return False


def main():
    while True:
        try:
            choice = draw_menu()
        except KeyboardInterrupt:
            clr()
            break

        if choice in ("00","0","quit","q","exit"):
            clr()
            bye_color = th()["primary"]
            bye_msg = t("bye")
            # Un objet Align interpole dans une f-string affiche son repr :
            # il doit etre passe tel quel a console.print().
            console.print()
            console.print(Align.center(Text(bye_msg, style=f"bold {bye_color}")))
            console.print()
            break

        if choice == KONAMI_TRIGGER:
            clr()
            banner()
            _run_action(konami_unlock, "99")
            pause()
            continue

        if choice.startswith("*") and choice[1:].strip():
            # *08 (dé)favorise le module 08 sans y entrer.
            raw_code = choice[1:].strip()
            code = raw_code.zfill(2) if raw_code.isdigit() else None
            if code is None:
                hits = find_module(raw_code)
                code = hits[0][0] if len(hits) == 1 else None
            if code and code in ACTIONS and code != "00":
                label, _ = _color_for(code)
                if code in FAVORITES:
                    FAVORITES.discard(code)
                    _save_prefs()
                    success(f"[bold]{esc(label)}[/bold] retiré des favoris.")
                elif len(FAVORITES) >= 12:
                    error("12 favoris maximum — retires-en un dans le module 59 (Préférences).")
                else:
                    FAVORITES.add(code)
                    _save_prefs()
                    success(f"[bold]{esc(label)}[/bold] ajouté aux favoris (★).")
            else:
                error(f"Aucun module ne correspond à « {esc(raw_code)} » (ex: *08).")
            time.sleep(0.8)
            continue

        fn = ACTIONS.get(choice) or ACTIONS.get(choice.zfill(2))
        if fn is None and choice and not choice.isdigit():
            # On peut taper un nom de module au lieu de son numero.
            hits = find_module(choice)
            if len(hits) == 1:
                choice, fn = hits[0][0], ACTIONS.get(hits[0][0])
            elif hits:
                clr(); banner()
                console.print(f"  [{th()['primary']}]{len(hits)} modules correspondent "
                              f"a « {esc(choice)} » :[/{th()['primary']}]\n")
                for code, label in hits[:15]:
                    console.print(f"    [{th()['accent']}]{code}[/{th()['accent']}]  {esc(label)}")
                pause()
                continue

        if fn:
            if choice.zfill(2) in ("20", "27"):
                _run_action(fn, choice); continue
            label, color = _color_for(choice)
            section(label, color)
            _run_action(fn, choice)
        else:
            console.print(f"  [{th()['danger']}]{t('err')}[/{th()['danger']}]")
            if choice and not choice.isdigit():
                console.print(f"  [dim]Aucun module ne correspond a « {esc(choice)} ».[/dim]")
                time.sleep(1.2)
            else:
                time.sleep(0.6)
            continue
        pause()


def _parse_args():
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description=f"{TOOL_NAME} — multi-tool terminal (systeme, reseau, monitoring, utilitaires).",
        epilog=(
            "Exemples :\n"
            f"  {TOOL_NAME} --list\n"
            f"  {TOOL_NAME} --run 08 --answer 1.1.1.1 --answer 3\n"
            f"  {TOOL_NAME} --run 55 --answer github.com --out cert.json\n"
            f"  {TOOL_NAME} --run 01 --json | jq .rows\n"
            "\nUne reponse commencant par '-' doit utiliser la forme collee :\n"
            f"  {TOOL_NAME} --run 52 --answer='-[0-9]+' --answer 'a -12 b'\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"{TOOL_NAME} {VERSION}")
    parser.add_argument("--no-update", action="store_true",
                        help="ne pas verifier les mises a jour au demarrage")
    parser.add_argument("--theme", choices=sorted(visible_theme_names()),
                        help="theme visuel a utiliser au demarrage")
    parser.add_argument("--lang", choices=("fr", "en"), help="langue de l'interface")
    parser.add_argument("--debug", action="store_true",
                        help="afficher les traces completes en cas d'erreur")
    parser.add_argument("--ascii", action="store_true",
                        help="remplacer les emoji par des equivalents lisibles "
                             "dans toutes les consoles (console Windows classique)")
    parser.add_argument("--keytest", action="store_true",
                        help="afficher les codes envoyes par le clavier et quitter "
                             "(diagnostic des touches flechees)")
    parser.add_argument("--list", action="store_true",
                        help="lister les modules disponibles et quitter")
    parser.add_argument("--run", metavar="CODE",
                        help="executer un module puis quitter (ex: --run 08)")
    parser.add_argument("--answer", metavar="VALEUR", action="append", default=[],
                        help="reponse fournie aux invites du module, dans l'ordre "
                             "(repetable ; les invites suivantes prennent leur valeur par defaut)")
    parser.add_argument("--json", action="store_true",
                        help="avec --run : afficher le resultat en JSON sur la sortie standard")
    parser.add_argument("--out", metavar="FICHIER",
                        help="avec --run : ecrire le resultat dans un fichier "
                             "(.json, .csv ou .html selon l'extension)")
    return parser.parse_args()


def list_modules():
    for title, color, items in get_cats():
        console.print(f"\n  [bold {color}]{title}[/bold {color}]")
        for code, label in items:
            if code == "00":
                continue
            console.print(f"    [{th()['accent']}]{code}[/{th()['accent']}]  {esc(label)}")
    console.print()


def run_headless(args):
    global HEADLESS
    HEADLESS = True
    code = args.run.zfill(2)
    fn = ACTIONS.get(code) or ACTIONS.get(args.run)
    if not fn:
        console.print(f"  [red]Module inconnu : {esc(args.run)}[/red] "
                      f"[dim](--list pour la liste)[/dim]")
        return 2

    answers = iter(args.answer)
    feed = lambda *a, **k: next(answers, "")

    label, _ = _color_for(code)
    LAST_RESULT["title"] = label if label != code else fn.__name__

    # Avec --json seul, l'affichage du module part dans le vide pour que la
    # sortie standard ne contienne que du JSON exploitable par un script.
    quiet = args.json and not args.out
    target = Console(file=io.StringIO(), width=200, highlight=False) if quiet else console
    # L'invite doit etre neutralisee sur la console REELLEMENT utilisee,
    # sinon le module attend une saisie clavier et le processus se fige.
    target.input = feed
    getpass.getpass = feed

    saved, globals()["console"] = console, target
    try:
        ok = _run_action(fn, code)
    finally:
        globals()["console"] = saved

    rows = _export_rows()
    cols = LAST_RESULT["columns"] or []

    if args.out:
        ext = os.path.splitext(args.out)[1].lstrip(".").lower() or "json"
        if ext not in ("json", "csv", "html"):
            error(f"Extension non geree : .{esc(ext)} (attendu json, csv ou html)")
            return 2
        if not rows:
            error("Ce module n'a produit aucun tableau exportable.")
            return 1
        try:
            write_export(os.path.abspath(os.path.expanduser(args.out)), ext,
                         LAST_RESULT["title"] or code, cols, rows)
        except OSError as e:
            error(f"Ecriture impossible : {esc(e)}")
            return 1
        success(f"Exporte : {esc(args.out)}")

    if args.json:
        print(json.dumps({
            "tool": TOOL_NAME, "version": VERSION, "module": code,
            "title": LAST_RESULT["title"], "ok": bool(ok),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "columns": cols,
            "rows": [dict(zip(cols, r)) for r in rows],
        }, indent=2, ensure_ascii=False))

    return 0 if ok else 1


if __name__ == "__main__":
    global_args = _parse_args()
    if global_args.debug:
        DEBUG = True
    if global_args.ascii:
        ASCII_MODE = True
    if global_args.no_update:
        UPDATE_ENABLED = False
    if global_args.theme:
        CURRENT_THEME_IDX = THEME_NAMES.index(global_args.theme)
    if global_args.lang:
        LANG = global_args.lang

    if global_args.keytest:
        keytest()
        sys.exit(0)

    if global_args.list:
        list_modules()
        sys.exit(0)

    if global_args.run:
        # Mode non interactif : ni banniere, ni menu, ni verification de MAJ.
        try:
            sys.exit(run_headless(global_args))
        except KeyboardInterrupt:
            sys.exit(130)

    try:
        if UPDATE_ENABLED:
            try:
                check_for_updates()
            except Exception as exc:
                # Une erreur de verification ne doit jamais empecher
                # l'outil de demarrer.
                warn(f"Verification de mise a jour ignoree ({type(exc).__name__}).")
        main()
    except KeyboardInterrupt:
        clr()
        sys.exit(0)
    except Exception:
        clr()
        console.print("  [red]Erreur fatale.[/red]")
        raw_print(traceback.format_exc())
        sys.exit(1)
