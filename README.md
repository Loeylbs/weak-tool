# 🛠️ WEAK Tool — Multi-Tool Terminal `v4.1.0`

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-personal_project-orange.svg)

**WEAK Tool** (aussi appelé *PRIME TOOL* dans le script) est un multi-outil tout-en-un s'exécutant directement dans ton terminal. Développé en Python, il regroupe une large collection d'utilitaires système, réseau, de sécurité et de monitoring sous une interface colorée et interactive.

## 📝 About

This project is made purely for fun and learning. I enjoy building my own tools and experimenting with Python. I don't recommend using it as your main tool — there are probably better and more complete alternatives. This is just a personal project with no real purpose beyond learning and enjoyment.

---

## 🚀 What's New in v4.1.0

La version **v4.1.0** ajoute **9 nouvelles fonctionnalités** majeures réparties dans les catégories Sécurité, Système, Réseau et Utilitaires — portant le projet à un total impressionnant de **37 outils** dans un seul et unique script.

### ✨ New Features

#### 🔐 Sécurité
* **[29] Firewall Rules :** Visualisation des règles de pare-feu actives (`iptables` / `nftables` / `ufw` sur Linux, `netsh` sur Windows) avec code couleur clair (ACCEPT/DROP/REJECT).
* **[30] SSH Audit :** Analyse le fichier `sshd_config`, vérifie 13 paramètres de sécurité critiques et attribue un score de fiabilité sur /100.

#### 🖥️ Système
* **[31] Watcher Logs :** Suivi en temps réel des logs (tail -f) avec colorisation automatique (`ERROR` = rouge, `WARN` = jaune, `DENIED` = rouge gras).
* **[32] Services Manager :** Liste tous les services système avec leur statut actuel et leur PID (`systemctl` sur Linux, `sc query` on Windows).
* **[33] Env Inspector :** Exploration des variables d'environnement avec option de filtrage. Les valeurs sensibles (tokens, clés d'API...) sont masquées automatiquement.
* **[37] Cron Inspector :** Inspecte la crontab de l'utilisateur ainsi que les dossiers cron système (`schtasks` sur Windows).

#### 🌐 Réseau
* **[34] ARP Table :** Affiche la table ARP locale et intègre une détection des doublons d'adresses MAC (alerte en cas d'ARP spoofing).
* **[35] Net Connections :** Liste toutes les connexions TCP/UDP actives triées par état, incluant le PID et le nom du processus associé.

#### 🛠️ Utilitaires
* **[36] File Hasher :** Calcule les empreintes de fichiers avec de nombreux algorithmes (MD5, SHA1, SHA256, SHA512, SHA3-256, BLAKE2b) et propose une vérification d'intégrité optionnelle face à un hash de référence.

---

## 📋 All 37 Tools

<details>
<summary><b>Clique ici pour dérouler la liste complète des 37 outils disponibles 🔓</b></summary>

* **💻 SYSTÈME :** `[01]` Info Système · `[02]` CPU · `[03]` RAM · `[04]` Disque · `[05]` Uptime · `[06]` Export Rapport
* **🌐 RÉSEAU :** `[07]` Info Réseau · `[08]` Ping · `[09]` Stats · `[10]` DNS · `[11]` Ports · `[12]` Scan LAN
* **📊 MONITORING :** `[13]` Live Monitor · `[14]` Top Processus
* **🛠️ UTILITAIRES :** `[15]` Hash · `[16]` Générateur MDP · `[17]` Testeur MDP · `[18]` Base64 · `[19]` Clean Temp
* **⚙️ AVANCÉ :** `[21]` Traceroute · `[22]` Whois/GeoIP · `[23]` QR ASCII · `[24]` Convertisseur · `[25]` Proc. Suspects · `[26]` Speedtest
* **🔥 NOUVEAU v4.1 :** `[29]` Firewall Rules · `[30]` SSH Audit · `[31]` Watcher Logs · `[32]` Services Manager · `[33]` Env Inspector · `[34]` ARP Table · `[35]` Net Connections · `[36]` File Hasher · `[37]` Cron Inspector
</details>

---

## 🎨 Themes

Personnalise ton expérience visuelle dans le terminal ! Tu peux changer de thème à tout moment via l'option `[27]` :
* 🔵 **Cyber**
* 🟢 **Matrix**
* 🔴 **Blood**
* 👻 **Ghost**

---

## ⚡ Install & Run

### Prérequis
* **Python 3.8 ou version supérieure** requis.

### Installation
Installe manuellement les dépendances principales via `pip` :
```bash
pip install rich psutil pyfiglet
