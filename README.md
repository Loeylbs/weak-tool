# 🛠️ weak-tool — Multi-Tool Terminal

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey" alt="Plateformes">
  <img src="https://img.shields.io/badge/version-1.3.0-brightgreen" alt="Version">
</p>

**weak-tool** (nom affiché par défaut : *weak-tool*, entièrement personnalisable) est un outil terminal tout-en-un pour l'administration système, le diagnostic réseau et le monitoring, écrit en Python avec une interface colorée grâce à [rich](https://github.com/Textualize/rich).

Plus de 47 fonctionnalités réparties en 5 catégories, 7 thèmes visuels, des contours de menu animés, une mise à jour automatique depuis GitHub, et un pseudo d'affichage personnalisable.

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

Le menu principal garde les panneaux centrés et les contours changent de couleur en continu pendant la saisie du choix.
                         / WEAK-TOOL \

      v1.3.0 · USER · toi@ton-pc · 14:32:07 · theme:Neon Board

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
| 32 | Services Manager |
| 33 | Env Inspector |
| 37 | Cron Inspector |
| **41** | **Diskpart Simplifié** |

### 🌐 RÉSEAU
| # | Action |
|---|--------|
| 07 | Info Réseau |
| 08 | Test Ping |
| 09 | Stats Réseau |
| 10 | Lookup DNS |
| 11 | Check Ports |
| 12 | Scan LAN |
| 29 | Firewall Rules |
| 30 | SSH Audit |
| 34 | ARP Table |
| 35 | Net Connections |
| 38 | Subnet Calc |
| 39 | MAC Lookup |

### 📊 MONITORING
| # | Action |
|---|--------|
| 13 | Moniteur Live |
| 14 | Top Processus |
| 31 | Watcher Logs |

### 🧰 UTILITAIRES
| # | Action |
|---|--------|
| 15 | Hash Generator |
| 16 | Générateur de mot de passe |
| 17 | Testeur de mot de passe |
| 18 | Outil Base64 |
| 19 | Nettoyer les fichiers temporaires |
| 36 | File Hasher |
| **42** | **Outils Texte** |
| **43** | **Date & Heure** |
| **44** | **Outils Couleur** |
| **45** | **Encodeurs (URL/HTML/Morse)** |
| **46** | **Générateur Aléatoire** |

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
| **40** | **Personnaliser le pseudo** |
| **47** | **Comparateur de textes** |

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
python3 weak-tool.py
```

Aucune installation manuelle de dépendances n'est nécessaire : le script détecte celles qui manquent et les installe via `pip` au premier lancement.

## Utilisation

```bash
python3 weak-tool.py
```

Tape le numéro de l'action souhaitée puis `Entrée` pour naviguer dans le menu. `00` permet de quitter à tout moment.

> 💡 Certaines fonctionnalités (Firewall Rules, SSH Audit, Services Manager, Env Inspector, Diskpart Simplifié...) donnent des informations plus complètes ou nécessitent des droits administrateur.

## Personnalisation

- **Changer de thème** (`27`) — 6 thèmes visuels : Neon Board, Graffiti, Cyber, Matrix, Blood, Dracula.
- **Changer de langue** (`20`) — bascule entre français et anglais.
- **Personnaliser le pseudo** (`40`) — remplace le nom affiché dans la bannière (lettres, chiffres, espaces, `-`/`_`, sans accents pour un rendu ASCII propre). Le choix est sauvegardé et repris automatiquement à chaque lancement.

## Mise à jour automatique

Au démarrage, l'outil vérifie si une nouvelle version est disponible dans les [releases GitHub](https://github.com/Loeylbs/weak-tool/releases) du dépôt, et propose de la télécharger et de l'installer automatiquement.

Si la version locale est supérieure à la dernière release publiée, l'outil détecte une version développeur et ignore la mise à jour pour éviter tout retour en arrière.

## Fichiers créés

Le script crée quelques petits fichiers cachés à côté de lui pour mémoriser tes préférences :

| Fichier | Rôle |
|---|---|
| `.weak-tool_update.json` | Suivi des vérifications/rappels de mise à jour |
| `.weak-tool_name.json` | Pseudo personnalisé sauvegardé |

## Avertissement

Les fonctionnalités réseau (Scan LAN, Check Ports, ARP Table, Net Connections...) sont conçues pour auditer **tes propres systèmes et réseaux**. Utilise-les uniquement sur du matériel que tu possèdes ou pour lequel tu as une autorisation explicite.

Le module **Diskpart Simplifié** (`41`) est destructif : il efface le disque sélectionné, recrée une partition principale, formate le volume, attribue une lettre et active la partition. Vérifie toujours le numéro, le modèle, la taille et les lettres affichées avant de confirmer.

## Changelog v1.3.0

- **Correction** : crash Unicode sur Windows lors de la vérification de mise à jour
- **Nouveaux modules** : Outils Texte, Date & Heure, Outils Couleur, Encodeurs (URL/HTML/Morse), Générateur Aléatoire, Comparateur de textes
- **Visuel** : nouveau thème Dracula, scan line animé dans le menu, barres de chargement, sparklines dans le moniteur live, rangées alternées dans les tableaux
- **Améliorations** : amorce du moniteur live plus fluide, transitions animées entre sections

---

<p align="center">Fait avec 🩷 par <a href="https://github.com/Loeylbs">Loeylbs</a></p>
