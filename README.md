[README.md](https://github.com/user-attachments/files/31320862/README.md)
<div align="center">

# weak-tool

**Un couteau suisse pour le terminal — système, réseau, monitoring et utilitaires.**

66 modules, 10 thèmes, un seul fichier Python.

[![Version](https://img.shields.io/badge/version-1.7.0-blue)](https://github.com/Loeylbs/weak-tool/releases)
[![Python](https://img.shields.io/badge/python-3.8%2B-green)](https://www.python.org/)
[![Plateformes](https://img.shields.io/badge/plateformes-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)](#compatibilité)

</div>

---

```
        ┌─── / SYSTÈME \ ────┐ ┌─── / RÉSEAU \ ─────┐ ┌─ / MONITORING \ ──┐
        │ [01] Info Système  │ │ [07] Info Réseau   │ │ [13] Moniteur Live│
        │ [02] Statut CPU    │ │ [08] Test Ping     │ │ [14] Top Processus│
        │ [03] Info RAM      │ │ [09] Stats Réseau  │ │ [65] Bilan Santé  │
        └────────────────────┘ └────────────────────┘ └───────────────────┘
```

## Sommaire

- [Installation](#installation)
- [Utilisation](#utilisation)
- [Les modules](#les-modules)
- [Ligne de commande](#ligne-de-commande)
- [Personnalisation](#personnalisation)
- [Configuration](#configuration)
- [Compatibilité](#compatibilité)

## Installation

Aucune installation à faire : le script récupère ses dépendances tout seul au
premier lancement.

```bash
git clone https://github.com/Loeylbs/weak-tool.git
cd weak-tool
python weak-tool.py
```

Ou téléchargez simplement `weak-tool.py` depuis les
[releases](https://github.com/Loeylbs/weak-tool/releases) et lancez-le.

Les dépendances installées automatiquement : `rich`, `psutil`, `pyfiglet`, `qrcode`.

## Utilisation

Lancez le script, puis tapez le numéro d'un module :

```bash
python weak-tool.py
```

Dans le menu :

| Saisie | Effet |
|---|---|
| `08` | ouvre le module 8 (Test Ping) |
| `ping` | recherche un module par son nom |
| `*08` | ajoute ou retire le module 8 des favoris |
| `00` | quitte |

Les favoris apparaissent dans un bandeau en haut du menu, avec une étoile.

## Les modules

<details open>
<summary><b>Système</b> — 14 modules</summary>

| | | | |
|---|---|---|---|
| `01` Info Système | `02` Statut CPU | `03` Info RAM | `04` Info Disque |
| `05` Uptime / Boot | `06` Exporter Rapport | `32` Gestionnaire Services | `33` Inspecteur d'Env |
| `37` Inspecteur Cron | `41` Diskpart Simplifié | `48` Espace Disque | `60` Batterie / Alim |
| `62` Intégrité Fichiers | `63` Benchmark | | |

</details>

<details open>
<summary><b>Réseau</b> — 16 modules</summary>

| | | | |
|---|---|---|---|
| `07` Info Réseau | `08` Test Ping | `09` Stats Réseau | `10` Lookup DNS |
| `11` Check Ports | `12` Scan LAN | `29` Règles Pare-feu | `30` Audit SSH |
| `34` Table ARP | `35` Connexions Réseau | `38` Calcul Sous-réseau | `39` Recherche MAC |
| `55` Inspecteur TLS | `56` En-têtes HTTP | `57` Enregistrements DNS | `64` Ports en Écoute |

</details>

<details open>
<summary><b>Monitoring</b> — 4 modules</summary>

| | | | |
|---|---|---|---|
| `13` Moniteur Live | `14` Top Processus | `31` Observateur de Logs | `65` Bilan de Santé |

</details>

<details>
<summary><b>Utilitaires</b> — 18 modules</summary>

| | | | |
|---|---|---|---|
| `15` Générateur de Hash | `16` Générateur Mdp | `17` Testeur Mdp | `18` Outil Base64 |
| `19` Nettoyer Temp | `36` Hash de Fichier | `42` Outils Texte | `43` Date & Heure |
| `44` Outils Couleur | `45` Encodeurs | `46` Générateur Aléatoire | `49` Gros Fichiers |
| `50` Doublons | `51` JSON / CSV / YAML | `52` Testeur Regex | `53` Explicateur Cron |
| `58` Décodeur JWT | `61` Phrase de Passe | | |

</details>

<details>
<summary><b>Avancé</b> — 13 modules</summary>

| | | | |
|---|---|---|---|
| `21` Traceroute | `22` Whois / GeoIP | `23` QR Code ASCII | `24` Convertisseur |
| `25` Proc. Suspects | `26` Speedtest | `40` Personnaliser Pseudo | `47` Comparateur |
| `54` Exporter Résultat | `28` Historique | `27` Changer Thème | `20` Langue (FR/EN) |
| `59` Préférences | | | |

</details>

### Quelques modules à connaître

**`65` Bilan de Santé** — dix contrôles pondérés (CPU, mémoire, disques,
température, batterie, uptime, ports exposés…) résumés en une note sur 100, avec
des recommandations qui renvoient vers les modules concernés.

**`55` Inspecteur TLS** — certificat, chaîne, dates d'expiration et protocoles
acceptés d'un domaine.

**`64` Ports en Écoute** — tous les services à l'écoute, avec le processus
propriétaire, et une alerte sur ceux joignables depuis le réseau.

**`62` Intégrité Fichiers** — empreinte d'une arborescence, puis détection des
fichiers ajoutés, modifiés ou supprimés depuis la dernière prise.

## Ligne de commande

Tous les modules fonctionnent aussi sans interface, ce qui permet de les
scripter :

```bash
# lister les modules disponibles
python weak-tool.py --list

# exécuter un module et sortir
python weak-tool.py --run 08 --answer 1.1.1.1 --answer 3

# récupérer le résultat en JSON
python weak-tool.py --run 01 --json | jq .rows

# écrire dans un fichier (.json, .csv ou .html selon l'extension)
python weak-tool.py --run 55 --answer github.com --out cert.json
```

| Option | Rôle |
|---|---|
| `--list` | liste les modules puis quitte |
| `--run CODE` | exécute un module puis quitte |
| `--answer VALEUR` | répond aux invites du module, dans l'ordre (répétable) |
| `--json` | affiche le résultat en JSON sur la sortie standard |
| `--out FICHIER` | écrit le résultat dans un fichier |
| `--theme NOM` | thème à utiliser au démarrage |
| `--lang fr\|en` | langue de l'interface |
| `--ascii` | remplace les emoji par des équivalents lisibles partout |
| `--no-update` | ne vérifie pas les mises à jour au démarrage |
| `--debug` | affiche les traces complètes en cas d'erreur |
| `--keytest` | diagnostic des touches fléchées |

## Personnalisation

### Thèmes

Dix thèmes, changeables à chaud avec le module `27` :

`Neon Board` · `Graffiti` · `Cyber` · `Matrix` · `Blood` · `Dracula` ·
`Blue_marine` · `Sunset` · `Arctic` · et un dixième à débloquer.

### Votre pseudo en bannière

Le module `40` permet de choisir le nom affiché en haut, sa **typographie**
(20 polices, avec aperçu avant validation) et son **style de couleur** :
dégradé horizontal, vague, dégradé vertical ou couleur unie.

### Animation du menu

Une traînée lumineuse parcourt le cadre des catégories. Elle ne s'active que
dans les terminaux qui composent l'image avant de l'afficher (Windows Terminal,
VS Code, ConEmu, terminaux Unix) — sur `cmd.exe` elle est coupée d'office pour
éviter tout scintillement.

Réglable dans le module `59` : `auto` (défaut), `soft` (forcée), `off`.

## Configuration

Trois fichiers sont créés à côté du script, en lecture seule pour votre
utilisateur :

| Fichier | Contenu |
|---|---|
| `.weak-tool_prefs.json` | thème, langue, favoris, animation |
| `.weak-tool_name.json` | pseudo, typographie, style de la bannière |
| `.weak-tool_update.json` | suivi des mises à jour |

## Compatibilité

- **Python** 3.8 ou plus récent
- **Windows**, **Linux**, **macOS**
- Certains modules (règles de pare-feu, gestionnaire de services, diskpart)
  demandent les droits administrateur et le signalent le cas échéant
- Aucun réseau n'est contacté sans action explicite de votre part

## Licence

Ce projet est distribué tel quel. Voir le fichier `LICENSE` s'il est présent.

---

<div align="center">
<sub>Il paraît qu'un vieux code de manette ouvre une porte dérobée dans le menu.</sub>
</div>
