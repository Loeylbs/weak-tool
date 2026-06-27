#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
  WEAK TOOL v2.0 — Multi-Tool Terminal
  pip install rich psutil pyfiglet
"""

import os, sys, socket, platform, time, hashlib, base64, random, string, getpass
import shutil
from datetime import datetime

# ── AUTO-INSTALL ──────────────────────────────────────────
def _ensure(*pkgs):
    import subprocess
    for p in pkgs:
        try:    __import__(p)
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", p, "-q"])
_ensure("rich", "psutil", "pyfiglet")

from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich.text    import Text
from rich.rule    import Rule
from rich.columns import Columns
from rich.align   import Align
from rich          import box
import psutil, pyfiglet

console = Console(width=shutil.get_terminal_size().columns)

# ── CONFIG ───────────────────────────────────────────────
TOOL_NAME = "PRIME" 
VERSION   = "v2.0"

# ── HELPERS ──────────────────────────────────────────────
def clr():  os.system("cls" if os.name == "nt" else "clear")

def pct_bar(pct, width=16):
    filled = max(0, int(pct / 100 * width))
    color  = "green" if pct < 60 else "yellow" if pct < 85 else "red"
    return f"[{color}]{'█'*filled}{'░'*(width-filled)}[/{color}]"

def pause():
    console.print()
    console.input("[dim]  ↵ Entrée...[/dim]")

# ── DÉCOR ────────────────────────────────────────────────
DOTS = "·  · · ·  · ·  · · ·  ·  · · ·  · ·  · · ·  ·  · · ·  · ·  · · ·  ·  ·"

def banner():
    clr()

    # ── fond de points ──
    console.print(f"[bright_black]{DOTS}[/bright_black]")
    console.print(f"[bright_black]{DOTS}[/bright_black]")
    console.print()

    # ── titre pixel ──
    ascii_logo = r"""
                                                      _______
                   __.....__                   .      \  ___ '.
       _     _ .-''         '.               .'|       ' |--.\  \.-.          .- .-''         '.
 /\    \\   ///     .-''"'-.  .           .'  |       | |    \  '\ \        / //     .-''"'-.  .
 \\  //\\ ///     /________\   \    __   <    |       | |     |  '\ \      / //     /________\   \
   \//  \'/ |                  | .:--.'.  |   | ____  | |     |  | \ \    / / |                  |
    \|   |/  \    .-------------'/ |   \ | |   | \ .'  | |     ' .'  \ \  / /  \    .-------------'
     '        \    '-.____...---." __ | | |   |/  .   | |___.' /'    \   /    \    '-.____...---.
               .             .'  .'.''| | |    /\  \ /_______.'/      \  /      .             .'
                 ''-...... -'   / /   | |_|   |  \  \\_______|/       / /         ''-...... -'
                                 \ \._,\ '/'    \  \  \            |-' /
                                  --'  "'------'  '---'           '..'
"""

    width = shutil.get_terminal_size().columns

    for line in ascii_logo.strip("\n").splitlines():
        console.print(f"[bold bright_cyan]{line.center(width)}[/bold bright_cyan]")

    # ── sous-titre ──
    console.print()
    console.print(Align.center(
        f"[dim]  {VERSION}  ·  {getpass.getuser()}@{platform.node()}"
        f"  ·  {datetime.now().strftime('%H:%M:%S')}  [/dim]"
    ))
    console.print()

# ── CATÉGORIES DU MENU ───────────────────────────────────
CATS = [
    ("SYSTÈME", "yellow", [
        ("01","System Info"),
        ("02","CPU Status"),
        ("03","RAM Info"),
        ("04","Disk Info"),
        ("05","Uptime / Boot"),
    ]),
    ("RÉSEAU", "green", [
        ("06","Network Info"),
        ("07","Ping Test"),
        ("08","Net Stats"),
        ("09","DNS Lookup"),
        ("10","Port Checker"),
    ]),
    ("MONITORING", "cyan", [
        ("11","Live Monitor"),
        ("12","Top Processus"),
    ]),
    ("UTILITAIRES", "magenta", [
        ("13","Hash Generator"),
        ("14","Password Gen"),
        ("15","Base64 Tool"),
        ("16","Clean Temp"),
        ("00","[ QUITTER ]"),
    ]),
]

def _make_panel(title: str, color: str, items: list) -> Panel:
    t = Text()
    for num, label in items:
        # Reprend le style de l'image : les crochets de la couleur du panel, le texte en blanc
        t.append(f"[{num}] ", style=f"bold {color}")
        t.append(f"{label}\n", style="white")
    
    # On enlève la dernière ligne vide pour que ce soit compact
    t.rstrip()
    
    return Panel(
        t,
        title=f"[bold {color}]/ {title} \\[/]",
        border_style=color,
        box=box.SQUARE, # Des angles bien droits
        expand=False,
        width=32 # Taille fixe pour qu'ils soient tous identiques
    )

def draw_menu() -> str:
    # 1. Le panel système centré en haut
    top_panel = _make_panel(*CATS[0])
    console.print(Align.center(top_panel))
    
    # 2. La ligne de connexion en pointillés stylée
    conn_line = (
        "[green]· · · · · · · [/green]"
        "[cyan]· · · · · · · [/cyan]"
        "[bright_black]· · · · · · · · · · · · · [/bright_black]"
        "[cyan]· · · · · · · [/cyan]"
        "[magenta]· · · · · · · [/magenta]"
    )
    console.print(Align.center(conn_line))
    
    # 3. Les 3 autres panels alignés avec une grille (Grid) pour un centrage parfait
    grid = Table.grid(padding=(0, 2)) # 2 espaces d'écart entre chaque menu
    grid.add_row(*[_make_panel(*c) for c in CATS[1:]])
    console.print(Align.center(grid))
    
    console.print()
    return console.input("[bold bright_cyan]  ❯ [/bold bright_cyan]").strip()

# ── SECTION HEADER ───────────────────────────────────────
def section(label: str, color: str):
    clr()
    banner()
    console.print(Rule(f"[bold {color}]◈  {label.upper()}  ◈[/bold {color}]",
                       style=f"dim {color}"))
    console.print()

def _color_for(choice: str) -> tuple:
    key = choice.zfill(2)
    for cat_title, cat_color, items in CATS:
        for num, label in items:
            if num == key:
                return label, cat_color
    return choice, "cyan"

# ═══════════════════════════════════════════════════════
#  FEATURES 
# ═══════════════════════════════════════════════════════

def system_info():
    u    = platform.uname()
    boot = datetime.fromtimestamp(psutil.boot_time())
    up   = str(datetime.now() - boot).split(".")[0]
    t    = Table(box=box.SQUARE, border_style="yellow")
    t.add_column("Propriété", style="yellow", width=18)
    t.add_column("Valeur",    style="white", width=50)
    t.add_row("OS",        f"{u.system} {u.release}")
    t.add_row("Version",   u.version[:52])
    t.add_row("Machine",   u.machine)
    t.add_row("Hostname",  u.node)
    t.add_row("User",      getpass.getuser())
    t.add_row("Python",    sys.version.split()[0])
    t.add_row("Uptime",    up)
    t.add_row("Boot",      boot.strftime("%Y-%m-%d %H:%M"))
    t.add_row("Processor", (u.processor or platform.processor())[:52])
    console.print(t)

def cpu_info():
    freq  = psutil.cpu_freq()
    usage = psutil.cpu_percent(interval=0.3)
    cores = psutil.cpu_percent(interval=0.3, percpu=True)
    t     = Table(box=box.SQUARE, border_style="yellow")
    t.add_column("", style="yellow", width=18)
    t.add_column("", style="white", width=50)
    t.add_row("Cœurs physiques",  str(psutil.cpu_count(logical=False)))
    t.add_row("Threads logiques", str(psutil.cpu_count(logical=True)))
    t.add_row("Usage global",     f"{pct_bar(usage)} [bold]{usage:.1f}%[/bold]")
    if freq:
        t.add_row("Fréquence", f"{freq.current:.0f} MHz  (max {freq.max:.0f} MHz)")
    t.add_row("─"*16, "─"*46)
    for i, c in enumerate(cores):
        t.add_row(f"  Core {i}", f"{pct_bar(c)} {c:.1f}%")
    console.print(t)

def ram_info():
    vm   = psutil.virtual_memory()
    swap = psutil.swap_memory()
    gb   = lambda n: f"{n/1e9:.2f} GB"
    t    = Table(box=box.SQUARE, border_style="yellow")
    t.add_column("", style="yellow", width=18)
    t.add_column("", style="white", width=50)
    t.add_row("Total",        gb(vm.total))
    t.add_row("Utilisée",     gb(vm.used))
    t.add_row("Libre",        gb(vm.available))
    t.add_row("Charge RAM",   f"{pct_bar(vm.percent)} [bold]{vm.percent}%[/bold]")
    t.add_row("─"*16, "─"*46)
    t.add_row("Swap Total",   gb(swap.total))
    t.add_row("Swap Utilisé", gb(swap.used))
    t.add_row("Charge Swap",  f"{pct_bar(swap.percent)} {swap.percent}%")
    console.print(t)

def disk_info():
    t = Table(box=box.SQUARE, border_style="yellow")
    t.add_column("Lecteur", style="yellow", width=12)
    t.add_column("Total",   style="white", width=10)
    t.add_column("Utilisé", style="white", width=10)
    t.add_column("Libre",   style="white", width=10)
    t.add_column("Charge",  style="white", width=26)
    for p in psutil.disk_partitions():
        try:
            u = psutil.disk_usage(p.mountpoint)
            t.add_row(p.device,
                      f"{u.total/1e9:.1f} GB", f"{u.used/1e9:.1f} GB",
                      f"{u.free/1e9:.1f} GB",  f"{pct_bar(u.percent)} {u.percent}%")
        except: pass
    console.print(t)

def uptime_info():
    boot = datetime.fromtimestamp(psutil.boot_time())
    up   = datetime.now() - boot
    h, r = divmod(int(up.total_seconds()), 3600);  m, s = divmod(r, 60)
    t    = Table(box=box.SQUARE, border_style="yellow")
    t.add_column("", style="yellow", width=18)
    t.add_column("", style="white", width=40)
    t.add_row("Boot time", boot.strftime("%Y-%m-%d %H:%M:%S"))
    t.add_row("Uptime",    f"[bold]{h}h {m}m {s}s[/bold]")
    console.print(t)

def network_info():
    hostname = socket.gethostname()
    try:    lip = socket.gethostbyname(hostname)
    except: lip = "N/A"
    net = psutil.net_io_counters()
    t   = Table(box=box.SQUARE, border_style="green")
    t.add_column("", style="green", width=22)
    t.add_column("", style="white", width=46)
    t.add_row("Hostname",  hostname)
    t.add_row("IP locale", lip)
    for iface, addrs in psutil.net_if_addrs().items():
        for a in addrs:
            if a.family == socket.AF_INET and a.address not in ("127.0.0.1","0.0.0.0"):
                t.add_row(f"  {iface}", a.address)
    t.add_row("─"*20, "─"*44)
    t.add_row("Envoyé",    f"{net.bytes_sent/1e6:.2f} MB")
    t.add_row("Reçu",      f"{net.bytes_recv/1e6:.2f} MB")
    t.add_row("Paquets ↑", str(net.packets_sent))
    t.add_row("Paquets ↓", str(net.packets_recv))
    console.print(t)

def ping_test():
    host = (console.input("[green]  Host [dim](défaut: google.com)[/dim] ❯ [/green]").strip()
            or "google.com")
    console.print(f"\n[dim green]Ping → {host}...[/dim green]\n")
    os.system(f"ping {host} {'-n' if os.name=='nt' else '-c'} 4")

def net_stats():
    t = Table(box=box.SQUARE, border_style="green")
    t.add_column("Interface", style="green", width=18)
    t.add_column("Envoyé",    style="white", width=14)
    t.add_column("Reçu",      style="white", width=14)
    t.add_column("Paquets ↑", style="white", width=12)
    t.add_column("Paquets ↓", style="white", width=12)
    for name, s in psutil.net_io_counters(pernic=True).items():
        t.add_row(name,
                  f"{s.bytes_sent/1e6:.1f} MB", f"{s.bytes_recv/1e6:.1f} MB",
                  str(s.packets_sent), str(s.packets_recv))
    console.print(t)

def dns_lookup():
    host = console.input("[green]  Domaine ❯ [/green]").strip()
    if not host:
        console.print("[red]  Rien fourni.[/red]"); return
    t = Table(box=box.SQUARE, border_style="green")
    t.add_column("Type",      style="green", width=10)
    t.add_column("Résultat",  style="white", width=52)
    try:    t.add_row("IPv4", socket.gethostbyname(host))
    except Exception as e: t.add_row("Erreur", str(e))
    try:
        for item in socket.getaddrinfo(host, None):
            if item[0].name == "AF_INET6":
                t.add_row("IPv6", item[4][0]); break
    except: pass
    console.print(t)

def port_checker():
    host = (console.input("[green]  Host [dim](défaut: localhost)[/dim] ❯ [/green]").strip()
            or "localhost")
    raw  = console.input("[green]  Ports [dim](ex: 80,443,8080 — vide=communs)[/dim] ❯ [/green]").strip()
    known = {21:"FTP",22:"SSH",25:"SMTP",53:"DNS",80:"HTTP",110:"POP3",
             143:"IMAP",443:"HTTPS",3306:"MySQL",5432:"PgSQL",6379:"Redis",
             8080:"HTTP-Alt",27017:"MongoDB"}
    ports = ([int(p) for p in raw.split(",") if p.strip().isdigit()]
             if raw else list(known.keys()))
    t = Table(box=box.SQUARE, border_style="green")
    t.add_column("Port",    style="green", width=8)
    t.add_column("État",    style="white", width=12)
    t.add_column("Service", style="dim",   width=18)
    for port in ports:
        try:
            s = socket.socket(); s.settimeout(0.8)
            open_ = s.connect_ex((host, port)) == 0; s.close()
            status = "[green]OUVERT[/green]" if open_ else "[red]FERMÉ[/red]"
        except: status = "[yellow]ERR[/yellow]"
        t.add_row(str(port), status, known.get(port,"—"))
    console.print(t)

def live_monitor():
    console.print("[dim cyan]  Ctrl+C pour arrêter[/dim cyan]\n")
    try:
        while True:
            clr(); banner()
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory().percent
            net = psutil.net_io_counters()
            dk  = psutil.disk_io_counters()
            t   = Table(title=f"[dim]🟢 Live — {datetime.now().strftime('%H:%M:%S')}[/dim]",
                        box=box.SQUARE, border_style="cyan")
            t.add_column("Métrique", style="cyan",  width=12)
            t.add_column("Barre",    style="white", width=20)
            t.add_column("Valeur",   style="white", width=12)
            col_c = "green" if cpu < 60 else "yellow" if cpu < 85 else "red"
            col_r = "green" if ram < 60 else "yellow" if ram < 85 else "red"
            t.add_row("CPU", pct_bar(cpu), f"[bold {col_c}]{cpu:.1f}%[/bold {col_c}]")
            t.add_row("RAM", pct_bar(ram), f"[bold {col_r}]{ram:.1f}%[/bold {col_r}]")
            t.add_row("Net ↑", f"[blue]{'▸'*16}[/blue]", f"[blue]{net.bytes_sent/1e6:.0f}MB[/blue]")
            t.add_row("Net ↓", f"[green]{'▸'*16}[/green]", f"[green]{net.bytes_recv/1e6:.0f}MB[/green]")
            if dk:
                t.add_row("Disk R", f"[magenta]{'▸'*16}[/magenta]", f"[magenta]{dk.read_bytes/1e6:.0f}MB[/magenta]")
                t.add_row("Disk W", f"[yellow]{'▸'*16}[/yellow]",   f"[yellow]{dk.write_bytes/1e6:.0f}MB[/yellow]")
            console.print(Align.center(t)); time.sleep(1)
    except KeyboardInterrupt: pass

def top_processes():
    procs = []
    for p in psutil.process_iter(["pid","name","cpu_percent","memory_info"]):
        try: procs.append(p.info)
        except: pass
    procs = sorted(procs, key=lambda x: x["cpu_percent"] or 0, reverse=True)[:15]
    t = Table(box=box.SQUARE, border_style="cyan")
    t.add_column("PID",   style="dim",   width=8)
    t.add_column("Nom",   style="white", width=26)
    t.add_column("CPU",   style="cyan",  width=8)
    t.add_column("RAM",   style="green", width=10)
    t.add_column("Barre", style="cyan",  width=20)
    for p in procs:
        cpu = p["cpu_percent"] or 0
        ram = (p["memory_info"].rss/1e6) if p["memory_info"] else 0
        t.add_row(str(p["pid"]), (p["name"] or "?")[:26],
                  f"{cpu:.1f}%", f"{ram:.0f} MB", pct_bar(min(cpu,100)))
    console.print(t)

def hash_gen():
    text = console.input("[yellow]  Texte ❯ [/yellow]")
    enc  = text.encode()
    t    = Table(box=box.SQUARE, border_style="magenta")
    t.add_column("Algo",     style="magenta", width=10)
    t.add_column("Résultat", style="white",  width=70)
    t.add_row("MD5",    hashlib.md5(enc).hexdigest())
    t.add_row("SHA1",   hashlib.sha1(enc).hexdigest())
    t.add_row("SHA256", hashlib.sha256(enc).hexdigest())
    t.add_row("SHA512", hashlib.sha512(enc).hexdigest())
    t.add_row("Base64", base64.b64encode(enc).decode())
    console.print(t)

def password_gen():
    try:   n = int(console.input("[yellow]  Longueur [dim](défaut 16)[/dim] ❯ [/yellow]") or "16")
    except: n = 16
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    t = Table(box=box.SQUARE, border_style="magenta")
    t.add_column("#",             style="dim magenta", width=4)
    t.add_column("Mot de passe",  style="bold white", width=60)
    for i in range(4):
        t.add_row(str(i+1), ''.join(random.choice(chars) for _ in range(n)))
    console.print(t)

def base64_tool():
    mode = console.input("[yellow]  (e)ncoder / (d)écoder ❯ [/yellow]").strip().lower()
    text = console.input("[yellow]  Texte ❯ [/yellow]")
    t    = Table(box=box.SQUARE, border_style="magenta")
    t.add_column("Action",   style="magenta", width=10)
    t.add_column("Résultat", style="white",  width=62)
    try:
        if mode in ("e","encode","encoder"):
            t.add_row("Encodé", base64.b64encode(text.encode()).decode())
        else:
            t.add_row("Décodé", base64.b64decode(text.encode()).decode())
    except Exception as e:
        t.add_row("[red]Erreur[/red]", str(e))
    console.print(t)

def clean_temp():
    console.print("[magenta]  Nettoyage...[/magenta]")
    if os.name == "nt": os.system("del /q /f /s %temp%\\* >nul 2>&1")
    else:               os.system("rm -rf /tmp/* 2>/dev/null")
    console.print("[green]  ✔ Fichiers temporaires supprimés ![/green]")

# ── ROUTER ───────────────────────────────────────────────
ACTIONS = {
    "01": system_info,  "1":  system_info,
    "02": cpu_info,     "2":  cpu_info,
    "03": ram_info,     "3":  ram_info,
    "04": disk_info,    "4":  disk_info,
    "05": uptime_info,  "5":  uptime_info,
    "06": network_info, "6":  network_info,
    "07": ping_test,    "7":  ping_test,
    "08": net_stats,    "8":  net_stats,
    "09": dns_lookup,   "9":  dns_lookup,
    "10": port_checker,
    "11": live_monitor,
    "12": top_processes,
    "13": hash_gen,
    "14": password_gen,
    "15": base64_tool,
    "16": clean_temp,
}

# ── MAIN ─────────────────────────────────────────────────
def main():
    while True:
        banner()
        choice = draw_menu()

        if choice in ("00","0"):
            clr()
            console.print()
            console.print(Align.center("[bold bright_cyan]À plus ![/bold bright_cyan]"))
            console.print()
            break

        fn = ACTIONS.get(choice)
        if fn:
            label, color = _color_for(choice)
            section(label, color)
            fn()
        else:
            console.print("  [red]Choix invalide.[/red]")

        pause()

if __name__ == "__main__":
    main()
