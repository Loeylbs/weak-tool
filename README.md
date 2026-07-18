# 🛠️ weak-tool — Multi-Tool Terminal

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey" alt="Plateformes">
  <img src="https://img.shields.io/badge/version-4.2.0-brightgreen" alt="Version">
</p>

**weak-tool** (nom affiché par défaut : *weakdye*, entièrement personnalisable) est un outil terminal tout-en-un pour l'administration système, le diagnostic réseau et le monitoring, écrit en Python avec une interface colorée grâce à [rich](https://github.com/Textualize/rich).

Près de 40 fonctionnalités réparties en 6 catégories, 4 thèmes visuels, une mise à jour automatique depuis GitHub, et un pseudo d'affichage personnalisable.

## 📋 Sommaire

- [Aperçu](#aperçu)
- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Personnalisation](#personnalisation)
- [Mise à jour automatique](#mise-à-jour-automatique)
- [Fichiers créés](#fichiers-créés)
- [Avertissement](#avertissement)
- [Licence](#licence)

## Aperçu

```
   ▄▀▄▀▄ ░▒▓█▓▒░ ▄▀▄▀▄ ░▒▓█▓▒░ ▄▀▄▀▄ ░▒▓█▓▒░ ▄▀▄▀▄

              [ bannière ASCII colorée, ton pseudo ]

      v4.2.0 · USER · toi@ton-pc · 14:32:07 · theme:Graffiti

  ┌─ / SYSTÈME [/] ────┐  ┌─ / RÉSEAU [/] ─────┐  ┌─ / MONITORING [/] ─┐
  │ [01] Info Système  │  │ [07] Info Réseau    │  │ [13] Moniteur Live │
  │ [02] Statut CPU     │  │ [08] Test Ping      │  │ [14] Top Processus │
  │ [03] Info RAM       │  │ [09] Stats Réseau   │  └─────────────────────┘
  │  ...                │  │  ...                │
  └─────────────────────┘  └─────────────────────┘
```

## Fonctionnalités

### 🖥️ SYSTÈME
| # | Action |
|---|--------|
| 01 | Info Système |
| 02 | Statut CPU |
| 03 | Info RAM |
| 04 | Info Disque |
| 05 | Uptime / Boot |
| 06 | Exporter Rapport |

### 🌐 RÉSEAU
| # | Action |
|---|--------|
| 07 | Info Réseau |
| 08 | Test Ping |
| 09 | Stats Réseau |
| 10 | Lookup DNS |
| 11 | Check Ports |
| 12 | Scan LAN |

### 📊 MONITORING
| # | Action |
|---|--------|
| 13 | Moniteur Live |
| 14 | Top Processus |

### 🧰 UTILITAIRES
| # | Action |
|---|--------|
| 15 | Hash Generator |
| 16 | Générateur de mot de passe |
| 17 | Testeur de mot de passe |
| 18 | Outil Base64 |
| 19 | Nettoyer les fichiers temporaires |

### 🔬 AVANCÉ
| # | Action |
|---|--------|
| 20 | Langue (FR/EN) |
| 21 | Traceroute |
| 22 | Whois / GeoIP |
| 23 | QR Code ASCII |
| 24 | Convertisseur (unités) |
| 25 | Processus suspects |
| 26 | Speedtest |
| 27 | Changer de thème |
| 28 | Historique des commandes |

### 🆕 NOUVEAU v4.2
| # | Action |
|---|--------|
| 29 | Firewall Rules |
| 30 | SSH Audit |
| 31 | Watcher Logs |
| 32 | Services Manager |
| 33 | Env Inspector |
| 34 | ARP Table |
| 35 | Net Connections |
| 36 | File Hasher |
| 37 | Cron Inspector |
| 38 | Subnet Calc |
| 39 | MAC Lookup |
| **40** | **Personnaliser le pseudo** |

## Prérequis

- Python **3.8 ou supérieur**
- Windows, Linux ou macOS
- Une connexion internet au premier lancement (installation automatique des dépendances manquantes)

Dépendances (installées automatiquement si absentes) :

- [`rich`](https://pypi.org/project/rich/) — interface terminal colorée
- [`psutil`](https://pypi.org/project/psutil/) — infos système / processus
- [`pyfiglet`](https://pypi.org/project/pyfiglet/) — bannière ASCII
- [`qrcode`](https://pypi.org/project/qrcode/) — génération de QR codes

## Installation

```bash
git clone https://github.com/Loeylbs/weak-tool.git
cd weak-tool
python3 ultimatetool.py
```

Aucune installation manuelle de dépendances n'est nécessaire : le script détecte celles qui manquent et les installe via `pip` au premier lancement.

## Utilisation

```bash
python3 ultimatetool.py
```

Tape le numéro de l'action souhaitée puis `Entrée` pour naviguer dans le menu. `00` permet de quitter à tout moment.

> 💡 Certaines fonctionnalités (Firewall Rules, SSH Audit, Services Manager, Env Inspector...) donnent des informations plus complètes si le script est lancé en administrateur (Windows) ou avec `sudo` (Linux/macOS).

## Personnalisation

- **Changer de thème** (`27`) — 4 thèmes visuels : Graffiti, Cyber, Matrix, Blood.
- **Changer de langue** (`20`) — bascule entre français et anglais.
- **Personnaliser le pseudo** (`40`) — remplace le nom affiché dans la bannière (lettres, chiffres, espaces, `-`/`_`, sans accents pour un rendu ASCII propre). Le choix est sauvegardé et repris automatiquement à chaque lancement.

## Mise à jour automatique

Au démarrage, l'outil vérifie si une nouvelle version est disponible dans les [releases GitHub](https://github.com/Loeylbs/weak-tool/releases) du dépôt, et propose de la télécharger et de l'installer automatiquement.

## Fichiers créés

Le script crée quelques petits fichiers cachés à côté de lui pour mémoriser tes préférences :

| Fichier | Rôle |
|---|---|
| `.weakdye_update.json` | Suivi des vérifications/rappels de mise à jour |
| `.weakdye_name.json` | Pseudo personnalisé sauvegardé |

## Avertissement

Les fonctionnalités réseau (Scan LAN, Check Ports, ARP Table, Net Connections...) sont conçues pour auditer **tes propres systèmes et réseaux**. Utilise-les uniquement sur du matériel que tu possèdes ou pour lequel tu as une autorisation explicite.

## Licence

Aucune licence n'est définie pour ce dépôt. Ajoute un fichier `LICENSE` (par exemple [MIT](https://choosealicense.com/licenses/mit/)) si tu veux préciser les conditions de réutilisation du projet.

---

<p align="center">Fait avec 🩷 par <a href="https://github.com/Loeylbs">Loeylbs</a></p>
