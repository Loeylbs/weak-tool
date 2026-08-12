# 🛠️ weak-tool — Multi-Tool Terminal

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey" alt="Plateformes">
  <img src="https://img.shields.io/badge/version-1.5.0-brightgreen" alt="Version">
</p>

**weak-tool** (nom affiché par défaut : *weak-tool*, entièrement personnalisable) est un outil terminal tout-en-un pour l'administration système, le diagnostic réseau et le monitoring, écrit en Python avec une interface colorée grâce à [rich](https://github.com/Textualize/rich).

**59 modules** répartis en 5 catégories, **9 thèmes visuels**, un menu filtrable en direct pendant la frappe, des favoris mis en avant, des contours de menu animés, un mode non-interactif pour scripter l'outil, l'export de n'importe quel résultat en JSON/CSV/HTML, des préférences persistantes, et une mise à jour automatique vérifiée.

## 📋 Sommaire

- [Aperçu](#aperçu)
- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Personnalisation](#personnalisation)
- [Mise à jour automatique](#mise-à-jour-automatique)
- [Fichiers créés](#fichiers-créés)
- [Confidentialité](#confidentialité)
- [Avertissement](#avertissement)
- [Licence](#licence)

## Aperçu

```

Le menu principal garde les panneaux centrés, les contours changent de couleur en continu pendant la saisie,
et taper un mot grise en direct tout ce qui ne correspond pas.
                         / WEAK-TOOL \

      v1.5.0 · USER · toi@ton-pc · 14:32:07 · theme:Neon Board

              ┌────────────────── ★ FAVORIS ──────────────────┐
              │ ★08 Test Ping   ★15 Générateur de Hash        │
              └─────────────────────────────────────────────────┘

  ┌─ / SYSTÈME [/] ────┐  ┌─ / RÉSEAU [/] ─────┐  ┌─ / MONITORING [/] ─┐
  │ [01] Info Système  │  │ [07] Info Réseau    │  │ [13] Moniteur Live │
  │ [02] Statut CPU     │  │ [08] Test Ping      │  │ [14] Top Processus │
  │ [03] Info RAM       │  │ [09] Stats Réseau   │  └─────────────────────┘
  │  ...                │  │  ...                │
  └─────────────────────┘  └─────────────────────┘

                              ❯ ping
                        1 correspondance(s)
                  CPU 12.4%   RAM 41.8%   14:32:07
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
| **48** | **Espace Disque** |
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
| **55** | **Inspecteur TLS** |
| **56** | **En-têtes HTTP** |
| **57** | **Enregistrements DNS** |

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
| **49** | **Gros Fichiers** |
| **50** | **Doublons** |
| **51** | **JSON / CSV / YAML** |
| **52** | **Testeur Regex** |
| **53** | **Explicateur Cron** |
| **58** | **Décodeur JWT** |

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
| **54** | **Exporter Résultat** |
| **59** | **Préférences & Favoris** |

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

Options en ligne de commande :

| Option | Effet |
|---|---|
| `--version` | affiche la version et quitte |
| `--no-update` | ne vérifie pas les mises à jour au démarrage |
| `--theme <nom>` | démarre sur un thème précis (`neon`, `matrix`, `dracula`…) |
| `--lang fr\|en` | langue de l'interface |
| `--debug` | trace complète en cas d'erreur (équivaut à `WEAK_TOOL_DEBUG=1`) |
| `--list` | liste tous les modules et quitte |
| `--run CODE` | exécute un module puis quitte |
| `--answer VALEUR` | réponse fournie aux invites du module (répétable) |
| `--json` | avec `--run` : résultat en JSON sur la sortie standard |
| `--out FICHIER` | avec `--run` : écrit le résultat (`.json`, `.csv` ou `.html`) |

### Mode non-interactif

N'importe quel module s'exécute sans interface, ce qui rend l'outil scriptable :

```bash
weak-tool --list                                          # découvrir les codes
weak-tool --run 55 --answer github.com --out cert.json    # certificat TLS → fichier
weak-tool --run 08 --answer 1.1.1.1 --answer 3            # 3 pings vers 1.1.1.1
weak-tool --run 03 --json | jq '.rows[] | .Valeur'        # RAM en JSON, filtrée
weak-tool --run 16 --answer 32 --json                     # 5 mots de passe de 32 caractères
```

Les `--answer` alimentent les invites du module dans l'ordre ; toute invite sans réponse
disponible prend sa valeur par défaut. Une réponse commençant par `-` s'écrit collée :
`--answer='-[0-9]+'`.

Codes de sortie : `0` succès, `1` échec du module, `2` erreur d'invocation.

### Navigation dans le menu

- taper un **numéro** (`08`) exécute le module ;
- taper un **nom** (`ping`, `tls`, `hash`) le retrouve — plusieurs correspondances affichent la liste ;
- **filtre en direct** : dès la première lettre tapée, les modules qui ne correspondent pas se grisent instantanément dans tous les panneaux, avec le nombre de correspondances affiché sous le prompt ;
- **`*08`** (ou `*ping`) ajoute ou retire le module `08` des favoris sans y entrer ;
- les favoris apparaissent dans un bandeau **★ FAVORIS** dédié au-dessus du menu, en plus de l'étoile dans la liste (module `59` pour les gérer autrement) ;
- une jauge **CPU / RAM** et l'heure sont affichées en direct au pied du menu ;
- sur un terminal de moins de 40 lignes, le menu bascule automatiquement en affichage compact.

Tape le numéro de l'action souhaitée puis `Entrée` pour naviguer dans le menu. `00` permet de quitter à tout moment.

> 💡 Certaines fonctionnalités (Firewall Rules, SSH Audit, Services Manager, Env Inspector, Diskpart Simplifié...) donnent des informations plus complètes ou nécessitent des droits administrateur.

## Personnalisation

- **Préférences** (`59`) — thème, favoris, réinitialisation. **Le thème, la langue et les favoris sont désormais sauvegardés** et repris au lancement suivant (ils étaient perdus à chaque fermeture avant la v1.4.0).
- **Changer de thème** (`27`) — 9 thèmes visuels : Neon Board, Graffiti, Cyber, Matrix, Blood, Dracula, Blue Magic, **Sunset**, **Arctic**.
- **Changer de langue** (`20`) — bascule entre français et anglais.
- **Personnaliser le pseudo** (`40`) — remplace le nom affiché dans la bannière (lettres, chiffres, espaces, `-`/`_`, sans accents pour un rendu ASCII propre). Le choix est sauvegardé et repris automatiquement à chaque lancement.

## Export des résultats

Chaque tableau affiché est mémorisé au passage. Le module **`54` Exporter Résultat**
écrit le dernier résultat affiché — quel que soit le module qui l'a produit — en
**JSON**, **CSV** ou **HTML** (page autonome, thème sombre, en-têtes fixes).

Depuis la ligne de commande, `--out` fait la même chose sans passer par le menu :

```bash
weak-tool --run 35 --out connexions.html
weak-tool --run 14 --out processus.csv
```

## Mise à jour automatique

Au démarrage, l'outil vérifie si une nouvelle version est disponible dans les [releases GitHub](https://github.com/Loeylbs/weak-tool/releases) du dépôt, et propose de la télécharger et de l'installer automatiquement. `--no-update` désactive la vérification.

Si la version locale est supérieure à la dernière release publiée, l'outil détecte une version développeur et ignore la mise à jour pour éviter tout retour en arrière.

### Vérifications appliquées avant toute installation

Une mise à jour remplace le script qui s'exécute : c'est le point le plus sensible de l'outil. Depuis la v1.4.0, chaque étape est contrôlée.

1. **HTTPS obligatoire**, hôte restreint à `github.com` / `objects.githubusercontent.com` — vérifié aussi après redirection.
2. **SHA-256 comparé** à l'asset `weak-tool.py.sha256` publié à côté du script dans la release.
3. **Sans condensat publié**, l'empreinte du fichier reçu est affichée et l'installation demande une confirmation explicite (`OUI`).
4. Le fichier doit être **du Python valide** ressemblant à weak-tool — une page d'erreur HTML ou un téléchargement tronqué est rejeté.
5. **Sauvegarde `.bak` obligatoire**, restaurée automatiquement si le remplacement échoue.

> 📦 **Pour les mainteneurs** : publiez systématiquement un fichier `weak-tool.py.sha256`
> à côté du script dans la release. Sans lui, l'auto-update fonctionne mais retombe sur
> une confirmation manuelle à chaque fois.
> ```bash
> sha256sum weak-tool.py > weak-tool.py.sha256
> ```

## Fichiers créés

Le script crée quelques petits fichiers cachés à côté de lui pour mémoriser tes préférences :

| Fichier | Rôle |
|---|---|
| `.weak-tool_update.json` | Suivi des vérifications/rappels de mise à jour |
| `.weak-tool_name.json` | Pseudo personnalisé sauvegardé |
| `.weak-tool_prefs.json` | Thème, langue et favoris |

Ces fichiers sont écrits en `0600` (lisibles par le seul propriétaire).

## Sécurité

La v1.4.0 corrige 20 problèmes relevés lors d'un audit complet du code (voir `AUDIT.md`), dont trois critiques : l'auto-update sans vérification d'intégrité, la génération de mots de passe par un PRNG non cryptographique, et la suppression sans confirmation des répertoires temporaires.

Règles appliquées dans tout le fichier :

- aucun `subprocess` avec `shell=True`, aucune commande construite par concaténation ;
- toute entrée destinée à une commande externe est validée (`valid_host`, `ask_int`, regex stricte) ;
- toute donnée non fiable affichée est échappée (`esc` / `raw_print`) ;
- toute lecture réseau ou fichier est bornée (`read_capped`, `tail_lines`) ;
- tout ce qui doit être imprévisible vient de `secrets`, jamais de `random` ;
- toute opération destructive demande une confirmation explicite ;
- les fichiers de configuration sont écrits en `0600`.

Une erreur dans un module n'arrête plus l'outil : elle est isolée et renvoie au menu.

## Confidentialité

Depuis la v1.5.0, un avertissement 🔒 s'affiche avant tout module qui révèle des
informations sensibles à l'écran — utile en cas de partage d'écran, de stream ou
simplement si quelqu'un regarde par-dessus l'épaule :

| Module | Ce qui est révélé |
|---|---|
| `07` Info Réseau | IP publique, localisation approximative, FAI |
| `12` Scan LAN | appareils et IP du réseau local |
| `34` Table ARP | adresses IP/MAC du réseau local |
| `35` Connexions Réseau | connexions actives (services, hôtes distants) |
| `33` Inspecteur d'Env | variables d'environnement (parfois des secrets non détectés par le masquage automatique) |
| `16` Générateur Mdp | mots de passe générés affichés en clair |

## Avertissement

Les fonctionnalités réseau (Scan LAN, Check Ports, ARP Table, Net Connections...) sont conçues pour auditer **tes propres systèmes et réseaux**. Utilise-les uniquement sur du matériel que tu possèdes ou pour lequel tu as une autorisation explicite.

Le module **Diskpart Simplifié** (`41`) est destructif : il efface le disque sélectionné, recrée une partition principale, formate le volume, attribue une lettre et active la partition. Vérifie toujours le numéro, le modèle, la taille et les lettres affichées avant de confirmer.

Le module **Nettoyer les fichiers temporaires** (`19`) supprime des fichiers sur le disque. Depuis la v1.4.0 il affiche d'abord ce qu'il compte supprimer et attend la saisie de `SUPPRIMER` ; les fichiers récents et les répertoires de session sont protégés.

## Changelog v1.5.0

### Navigation

- **filtre en direct** dans le menu : les modules non correspondants se grisent au fil de la frappe, avec un compteur de correspondances
- **bandeau ★ FAVORIS** dédié, affiché au-dessus des catégories
- **raccourci `*08`** pour (dé)favoriser un module sans y entrer
- indice d'aide permanent en pied de menu

### Visuel

- **2 nouveaux thèmes** : Sunset (orange/rose) et Arctic (bleu glacé)
- **transition animée** à l'entrée dans un module (bordure qui tourne), au lieu d'un affichage instantané
- **jauge CPU/RAM live** + horloge en pied de menu
- correction : le thème Blue Magic n'affichait jamais son dégradé de bannière dédié (mauvaise clé de comparaison interne)

### Modules enrichis

- `15` Générateur de Hash — ajout de BLAKE2b et CRC32
- `16` Générateur Mdp — estimation du temps de cassage hors ligne affichée
- `17` Testeur Mdp — liste noire de mots de passe très courants (score plafonné + alerte)
- `01` Info Système — nombre de processus actifs et de sessions ouvertes
- `04` Info Disque — alerte si un disque dépasse 90 % d'occupation

### Confidentialité

- avertissement 🔒 avant l'affichage de données sensibles (IP, réseau local, variables d'environnement, mots de passe) — voir [Confidentialité](#confidentialité)

## Changelog v1.4.0

### Nouveautés

**12 nouveaux modules** (47 → 59)

| # | Module | Ce qu'il fait |
|---|---|---|
| 48 | Espace Disque | répartition de l'occupation par sous-répertoire, avec barres de proportion |
| 49 | Gros Fichiers | les plus gros fichiers d'une arborescence, au-dessus d'un seuil |
| 50 | Doublons | doublons par SHA-256 — compare tailles, puis préfixes, puis contenu complet |
| 51 | JSON / CSV / YAML | formater, valider (erreur pointée ligne/colonne), convertir, analyser |
| 52 | Testeur Regex | correspondances, positions, groupes nommés, alerte sur motif lent |
| 53 | Explicateur Cron | traduit une expression cron en français, valide chaque champ |
| 54 | Exporter Résultat | exporte le dernier tableau affiché en JSON / CSV / HTML |
| 55 | Inspecteur TLS | certificat, chaîne, protocole, expiration, SAN, protocoles obsolètes |
| 56 | En-têtes HTTP | HSTS, CSP, X-Frame-Options… avec score et détection de fuite de pile |
| 57 | Enregistrements DNS | A/AAAA/MX/NS/TXT/CNAME/SOA/CAA + lecture SPF et DMARC, via DNS-over-HTTPS |
| 58 | Décodeur JWT | en-tête et charge utile, expiration, alerte `alg=none` |
| 59 | Préférences | thème, favoris, réinitialisation — le tout sauvegardé |

**Confort d'usage**

- **préférences persistantes** — thème, langue et favoris repris au lancement suivant
- **recherche par nom** dans le menu : taper `ping` ou `tls` au lieu du numéro
- **favoris** marqués d'une ★ dans le menu
- **menu compact automatique** sur les terminaux de moins de 40 lignes
- **mode non-interactif** `--run` / `--answer` / `--json` / `--out` pour scripter l'outil
- `--list` pour découvrir les codes des modules

**Export**

- tout tableau affiché est exportable en JSON, CSV ou HTML — sans modifier les modules
- export HTML autonome (thème sombre, en-têtes fixes, contenu échappé)

### Sécurité — audit complet, 20 correctifs (détail dans `AUDIT.md`)

- 🔴 auto-update : HTTPS + hôte en liste blanche, vérification SHA-256, contrôle de sanité du fichier, sauvegarde obligatoire
- 🔴 génération de mots de passe et de jetons : passage de `random` (prévisible) à `secrets`
- 🔴 `clean_temp` : aperçu, filtre d'âge, chemins protégés, confirmation obligatoire
- 🟠 validation des hôtes et des noms de service (injection d'arguments dans `ping`, `traceroute`, `systemctl`…)
- 🟠 échappement de toute donnée non fiable affichée (logs, variables d'environnement, sorties de commandes)
- 🟠 lectures réseau et fichiers bornées ; `watcher_logs` ne charge plus le fichier entier en mémoire
- 🟠 `pass_checker` : saisie masquée ; `env_inspector` : détection de secrets par valeur
- 🟡 fichiers de configuration en `0600`, `-ExecutionPolicy Bypass` retiré, speedtest en HTTPS

### Corrections de plantage

- `re` et `uuid` n'étaient jamais importés — `color_tools` (RGB → Hex) plantait systématiquement
- `net_connections` plantait sur toute machine Linux (sockets UNIX)
- une erreur dans n'importe quel module tuait l'outil entier — chaque module est maintenant isolé
- l'auto-update était désactivé en permanence par une garde qui retournait toujours `None`
- `file_hasher` affiche enfin la taille et le débit qu'il calculait déjà

- `net_connections` corrigé aussi pour les sockets UNIX (protocole `UNIX` distingué)
- entropie affichée par le générateur de mots de passe

## Changelog v1.3.0

- **Correction** : crash Unicode sur Windows lors de la vérification de mise à jour
- **Nouveaux modules** : Outils Texte, Date & Heure, Outils Couleur, Encodeurs (URL/HTML/Morse), Générateur Aléatoire, Comparateur de textes
- **Visuel** : nouveau thème Dracula, scan line animé dans le menu, barres de chargement, sparklines dans le moniteur live, rangées alternées dans les tableaux
- **Améliorations** : amorce du moniteur live plus fluide, transitions animées entre sections

---

<p align="center">Fait avec 🩷 par <a href="https://github.com/Loeylbs">Loeylbs</a></p>
