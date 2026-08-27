# ROSMASTER R2 — PROJECT CONTEXT

## Projet

Développement et modification d'un **ROSMaster R2 YAHBOOM** sur **Raspberry Pi 5**.

Objectif : transformer/adapter le robot pour fonctionner avec notre propre
architecture de robot auto-équilibré et contrôler les moteurs avec notre propre
logiciel (PID + commande motrice maison).

---

## Historique du projet

### 2026-08-26 — Mise en place

- SSH ✅, Wi-Fi ✅, Internet ✅.
- Python 3.14.4 + pip 25.1.1 installés.
- Dépôt YAHBOOM cloné : `git clone https://github.com/YahboomTechnology/ROSMASTER-R2.git`.
- Carte détectée via `/dev/ttyUSB0` (CH340/341).
- `Rosmaster_Lib` V3.3.9 installée (zip officiel via Google Drive).
- Communication série validée : firmware V3.5, batterie 7,7 V, IMU + encodeurs reçus.

### 2026-08-27 — Tests moteurs et batterie 7,4 V

- Batterie remplacée par une **2S LiPo 7,4 V** (lue 7,10 V).
- Tests moteurs erratiques → hypothèse batterie faible (confirmée ensuite).
- **M1 + M3 (propulsion) validés** : avancent et reculent ensemble, trajectoire
  **tout droit** au sol.
- Seuils de démarrage : **M1 ≈ +25 PWM, M3 ≈ +20 PWM** → consigne ≥ +30.
- Carte reconfigurée **car_type = 5 (R2)**, persisté en flash.
- `set_car_motion` ne roule pas si le robot est incliné.
- **IMU live validée** (~10 Hz) ; découverte : carte IMU montée inclinée dans le
  châssis → l'équilibre se joue autour de pitch −40/−47°, PAS 0°.
- **PID d'équilibre `balance_pid.py`** : sonde OK, signe correct, anti-chute OK.

---

## État actuel

### Fonctionnel (confirmé)

- SSH ✅ / Wi-Fi ✅ / Internet ✅
- Python 3.14.4 ✅ / pip 25.1.1 ✅ / git 2.53.0 ✅ / OpenCode 1.18.22 ✅
- Dépôt `~/ROSMASTER-R2` cloné ✅
- Carte YB-ERF01 détectée sur `/dev/ttyUSB0` ✅
- `Rosmaster_Lib` V3.3.9 importable ✅
- Communication série (115200) validée ✅
- **Propulsion M1 + M3 validée** (avant + recul, tout droit) ✅
- IMU temps réel (~10 Hz) ✅
- Sonde PID d'équilibre : signe + correct, anti-chute ✅

### En cours

- **PID d'équilibre** : cible précise à affiner, KP croissant → vrai lâché.

### Scripts développés

| Fichier | Rôle |
|---------|------|
| `diagnostic.py` | Diagnostic complet sans moteur (série, firmware, batterie, buzzer, IMU, encodeurs, vitesse, PID) |
| `motor_test.py` | Test PWM brut 1er niveau (interactif, confirmation) |
| `motor_test_auto.py` | Test PWM brut automatisé (countdown) |
| `motor_diag.py` | Diagnostic M1/M3 répété (x2) |
| `motor_diag_BC.py` | Options B (M2/M4) et C (M3 croissant) |
| `motor_test_2mot.py` | Test propulsion R2 (M1+M3) sous 7,4 V |
| `motor_forward_2mot.py` | M1+M3 en avant, escalade +30/+45/+60 |
| `imu_live.py` | Lecture IMU temps réel (~10 Hz) |
| `balance_pid.py` | PID équilibre (modes `--dry` / `--probe`) |

Chemin projet : `/home/moise/ROSMASTER-R2`

---

## Matériel détecté

| Élément | Détail |
|---------|--------|
| Calculateur | Raspberry Pi 5 (aarch64) |
| OS | Ubuntu 26.04 LTS |
| Nom d'hôte | `R2D2` |
| Utilisateur | `moise` |
| Carte YAHBOOM | **YB-ERF01-V3.0** (firmware V3.5) |
| Convertisseur USB | CH340/CH341 — `idVendor=1a86`, `idProduct=7523` |
| Port série | `/dev/ttyUSB0` |
| IMU | MPU9250 (9 axes) soudé sur carte expansion |
| Batterie actuelle | **7,4 V nominal (2S LiPo)**, lue ~7,10 V |

---

## Communication Raspberry Pi ↔ PC

- Serveur SSH actif : `ssh moise@<IP>`.
- IP **dynamiques (DHCP)** observées successivement :
  192.168.137.152 → 192.168.137.96 → 192.168.137.48 (actuelle).
  Vérifier à chaque session avec `hostname -I`.
- Erreur résolue : `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!`
  → mise à jour de l'entrée dans `~/.ssh/known_hosts`.
- Internet OK (apt, pip, git).

---

## Communication Raspberry Pi ↔ carte YAHBOOM

Chaîne fonctionnelle (à respecter dans cet ordre) :

```
USB
 ↓
/dev/ttyUSB0 (115200 bauds, 8N1)
 ↓
Communication série (protocole YAHBOOM)
 ↓
Carte YB-ERF01
 ↓
IMU / Encodeurs / Vitesse / Moteurs
```

Protocole série :

- 115200 bauds, 8N1
- En-tête : `0xFF`
- Device ID : `0xFC`
- Complément : `257 - 0xFC = 0x03`
- Checksum : `(somme_bytes + complement) & 0xFF`

Auto-report firmware → Pi (4 paquets toutes les 40 ms) :

1. Vitesse (vx, vy, vz)
2. Données brutes MPU (gyro + accel raw)
3. Attitude IMU (roll, pitch, yaw)
4. Encodeurs (m1, m2, m3, m4)

NE PAS utiliser `/dev/myserial` tant qu'il n'a pas été recréé proprement →
utiliser `/dev/ttyUSB0`.

---

## Rosmaster_Lib

- Version : **V3.3.9** — installée ✅
- Package : `Rosmaster_Lib-3.3.9-py3.14.egg`
- Chemin : `/usr/local/lib/python3.14/dist-packages/`
- Source : `~/Rosmaster/py_install/Rosmaster_Lib/Rosmaster_Lib.py` (1331 lignes)
- Dépendance : pyserial 3.5
- Ne jamais utiliser un package pip aléatoire.

### Constructeur

```python
Rosmaster(car_type=1, com="/dev/myserial", delay=0.002, debug=False)
```

Notre usage :

```python
Rosmaster(car_type=5, com="/dev/ttyUSB0", delay=0.002, debug=False)
```

`car_type` : 1=X3, 2=X3+, 4=X1, **5=R2** (`CARTYPE_R2 = 0x05`).

### API principale

Moteurs / mouvement :

- `set_motor(s1, s2, s3, s4)` : PWM brut [-100,100], `127`=conserver, borné.
- `set_car_run(state, speed, adjust=False)` : state 0=stop…6=rotation droite.
- `set_car_motion(v_x, v_y, v_z)` : R2 → vx=[-1.8,1.8] m/s, vy=[-0.045,0.045],
  vz=[-3,3] rad/s (correction encodeurs interne).

IMU :

- `get_imu_attitude_data(ToAngle=True)` → roll, pitch, yaw
- `get_gyroscope_data()` → gx, gy, gz
- `get_accelerometer_data()` → ax, ay, az
- `get_magnetometer_data()` → mx, my, mz

Encodeurs / vitesse :

- `get_motor_encoder()` → m1, m2, m3, m4 (compteurs cumulés)
- `get_motion_data()` → vx, vy, vz (calcul firmware)

PID :

- `set_pid_param(kp, ki, kd, forever=False)` — PID de `set_car_motion`, plage [0,10]
- `get_motion_pid()` → [kp, ki, kd]

Utilitaires :

- `create_receive_threading()` — OBLIGATOIRE avant toute lecture ; une seule fois
- `set_auto_report_state(enable, forever=False)`
- `clear_auto_report_data()`
- `reset_car_state()`
- `reset_flash_value()` — retour usine (équiv. appui long K2)
- `set_beep(on_time)`
- `get_battery_voltage()` → V
- `get_version()`
- `get_car_type_from_machine()`
- `set_car_type(car_type)` — écrit en flash
- RGB : `set_colorful_lamps`, `set_colorful_effect` (non critiques)

---

## USB / port série

- Périphérique : `/dev/ttyUSB0` — `crw-rw---- root dialout`
- Convertisseur : **CH340/CH341** (`1a86:7523`)
- L'utilisateur `moise` ∈ groupe `dialout` (nécessaire pour accéder au port)
- `/dev/serial/by-id/` était vide à l'époque.
- `lsusb` détecte le périphérique.
- Si non dans dialout : `sudo usermod -aG dialout moise` puis nouvelle session.

### Historique d'installation de la lib

1. `from Rosmaster_Lib import Rosmaster` → **ModuleNotFoundError** au départ.
2. Téléchargement `py_install.zip` depuis `https://www.yahboom.net/.../py_install.zip`
   → fichier **0 octet** (HTTP 200 mais vide) → méthode **INVALIDÉE**.
3. **Installe réellement utilisée** : zip officiel `py_install_V3.3.9.zip`
   (via Google Drive) → `sudo python3 setup.py install` → egg installé ✅.
4. `pdftotext "3. Install Rosmaster driver library.pdf" ...` (poppler-utils)
   pour lire la notice depuis `04.ROS2-R2 Car Tutorial/05. Basic course/`.

---

## IMU

- Capteur : **MPU9250** (9 axes), soudé sur carte expansion.
- Lien : I2C (PB15=SDA, PB13=SCL, PB14=AD0) ; lecture ~10 ms par le firmware.
- Angles via fusion quaternion (DMP interne).
- Autres références doc : ICM20948 (selon version de carte).

### Constats mesurés (2026-08-27)

- Repos (pose A) : roll 15,9° / pitch **−40,4°** / yaw −68,9°.
- Repos (pose B) : roll 8,0° / pitch **−47,0°**.
- **Le pitch de repos varie avec la façon dont le robot est posé**.
- **Constat majeur** : la carte IMU est **montée inclinée dans le châssis** →
  la position « verticale/équilibre » du R2 se lit **≠ 0°**, plutôt **−40 à −47°**.

Pour l'auto-équilibrage, l'axe critique est le **pitch** (inclinaison avant/arrière).

---

## Encodeurs

- `get_motor_encoder()` → 4 compteurs cumulés (M1…M4) issus du firmware STM32.
- Le R2 n'utilise que 2 moteurs (M1, M3) mais reporte 4 compteurs.
- Lecture fiable ~20 Hz pendant les tests.
- Deltas utilisés pour valider le mouvement des roues (voir Moteurs).

---

## PID

### PID interne (carte / `set_car_motion`)

- Par défaut récupéré : **[Kp 0.8, Ki 0.06, Kd 0.5]**.
- Réglable via `set_pid_param(kp, ki, kd, forever)`.
- `set_car_motion(vx=0.3,0,0)` testé : **aucun mouvement** quand le robot est
  incliné (−40°) → le firmware R2 semble verrouiller le roulage hors position
  verticale. À re-tester debout.

### PID maison (mode équilibre — `balance_pid.py`)

- Boucle ~20 Hz : `pwm = KP*err + KD*derr`, `err = pitch - target`.
- Paramètres par args : `--kp --kd --target --sign --max --run`.
- Modes : `--dry` (calibrage sans moteur), `--probe` (robot sur cale, vérification
  du signe).
- Saturation PWM, arrêt auto si `|err| > 25°`, arrêt forcé dans `finally`.
- Sonde : **SIGN=+1 correct** (incliner en avant → roues poussent en avant),
  boucle live, anti-chute OK.
- Correctif : dérivée du 1er échantillon neutralisée.

### Architecture PID envisagée

```
PID équilibre
    ↓  correction principale
commande moteurs

Puis (plus tard, dans l'ordre) :
PID vitesse / encodeur
PID direction
PID rotation
```

Ne pas implémenter les PID avancés avant la commande moteur bas niveau validée.

---

## Moteurs

### Mapping physique R2

| Canal | Position | Rôle |
|-------|----------|------|
| M1 | haut gauche | **roue gauche** |
| M2 | bas gauche | non utilisé (R2 2-roues) |
| M3 | haut droit | **roue droite** |
| M4 | bas droit | non utilisé (R2 2-roues) |

`set_motor` pilote les 4 canaux en PWM brut, indépendamment du car_type.

### Résultats de tests — batterie 7,4 V (2S LiPo)

| Canal | Résultat |
|-------|----------|
| M1 (gauche) | ✅ tourne — seuil de démarrage ≈ +25 PWM |
| M2 (bas gauche) | ✅ tourne (+60, canal de secours possible) |
| M3 (droit) | ✅ tourne — dès +20 PWM |
| M4 (bas droit) | ❌ jamais observé (non requis sur R2) |

Tests de propulsion ensemble (deltas encodeurs) :

```
Encore dégagé du sol :
  +30 : M1=+322   M3=+524
  +45 : M1=+688   M3=+835
  +60 : M1=+1641  M3=+1349

Au sol :
  Avancer +30, 5s : M1=+1327  M3=+812
  Reculer -30, 5s : M1=-1757  M3=-1097
  -> Trajectoire TOUT DROIT en avant et en arrière (visuel utilisateur)
  -> Sens physique M1/M3 CONFORMES, propulsion R2 validée ✅
```

### Batterie 7,4 V — faits

- Nominal 7,4 V (2S LiPo) ; lue ~7,10 V ; le R2 vise DC 12 V → couple réduit ~38 %.
- Sous-tension : moteurs erratiques (tantôt M1, tantôt M3) → **ne jamais conclure
  « moteur mort » sous le seuil de démarrage**.
- Consigne fiable sous 7,4 V : **≥ +30 PWM**.
- Aucune carte moteur morte : l'échec précédent = batterie faible.

### `set_car_motion` testé

- `set_car_motion(0.3, 0, 0)` 2 s, robot incliné −40° → **0 mouvement**.
- Hypothèse : firmware R2 verrouille le roulage hors vertical.

---

## Problèmes rencontrés et solutions

| Problème | Cause | Solution |
|----------|-------|----------|
| `ModuleNotFoundError: Rosmaster_Lib` | lib absente | install zip officiel V3.3.9 (Google Drive) |
| `py_install.zip` 0 octet | serveur renvoie vide | méthode invalidée, utiliser le zip officiel |
| Moteurs erratiques / M3 « mort » | **batterie trop faible** | batterie 7,4 V 2S LiPo → M1+M3 validés |
| M1 immobile à +20 | seuil de démarrage ~+25 | tester ≥ +30 |
| `set_car_motion` sans effet | robot incliné | re-tester debout quand l'équilibre marche |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | IP/SSH change | mettre à jour `known_hosts` |
| Pitch de repos variable (−40/−47°) | pose du robot + IMU inclinée | cible d'équilibre à mesurer, pas figée |
| Pic de dérivée au 1er échantillon PID | dt ≈ 0 | neutraliser le premier calcul de dérivée |
| `pdftotext` absent | poppler-utils manquant | `sudo apt install poppler-utils` |
| Accès `/dev/ttyUSB0` refusé | permissions | `sudo usermod -aG dialout moise` + reconnexion |

---

## Commandes importantes

Réseau / machine :

```bash
hostname -I
uname -m
cat /etc/os-release
ssh moise@192.168.137.96
```

Outils :

```bash
python3 --version
pip3 --version
git --version
```

USB / série :

```bash
lsusb
ls -l /dev/ttyUSB*
groups
sudo dmesg | grep -Ei "usb|tty|serial|ch340|ch341"
```

Dépôt :

```bash
git clone https://github.com/YahboomTechnology/ROSMASTER-R2.git
cd "$HOME/ROSMASTER-R2"
git status
git log --oneline -10
git remote -v
```

Recherche code moteur YAHBOOM :

```bash
grep -Rni "set_motor" ~/ROSMASTER-R2 2>/dev/null
grep -Rni "Rosmaster\|ttyUSB\|encoder\|imu" ~/ROSMASTER-R2 2>/dev/null
```

PDF notice :

```bash
cd "$HOME/ROSMASTER-R2/04.ROS2-R2 Car Tutorial/05. Basic course"
pdftotext "3. Install Rosmaster driver library.pdf" /tmp/rosmaster_install.txt
```

Python :

```bash
python3 diagnostic.py          # diagnostic sans moteur
python3 motor_test_2mot.py     # test propulsion 7,4 V
python3 motor_forward_2mot.py  # escalade avant +30/+45/+60
python3 imu_live.py            # IMU temps réel
python3 balance_pid.py --probe --target -47.0
```

---

## Erreurs rencontrées et leur résolution

1. **`ModuleNotFoundError: No module named 'Rosmaster_Lib'`**
   - Cause : bibliothèque absente du système.
   - Résolution : installer le zip officiel V3.3.9 (Google Drive) via
     `sudo python3 setup.py install`.

2. **`py_install.zip` → HTTP 200 mais 0 octet**
   - Cause : ressource YAHBOOM serveur vide.
   - Résolution : abandonner cette URL, utiliser la source officielle.

3. **`WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!` (SSH)**
   - Cause : clé hôte modifiée (IP changeante / réinstallation).
   - Résolution : mettre à jour l'entrée dans `~/.ssh/known_hosts`.

4. **M3/M4 semblaient morts (diagnostic faussé)**
   - Cause : batterie 7,1 V trop faible (R2 prévu en 12 V).
   - Résolution : batterie 7,4 V → M1+M3 validés (voir Moteurs).

5. **M1 immobile à +20 PWM**
   - Cause : seuil de démarrage de M1 ≈ +25 sous 7,4 V.
   - Résolution : consigne ≥ +30.

6. **`set_car_motion` aucun effet (robot incliné)**
   - Cause : firmware R2 refuse de rouler hors vertical (hypothèse).
   - Résolution : à re-tester debout ; PID maison en attendant.

7. **Pic de dérivée au 1er échantillon de la boucle PID**
   - Cause : `dt` ≈ 0 initial.
   - Résolution : `pitch_prev = None` → `derr = 0` au 1er tour.

8. **`pdftotext` introuvable**
   - Cause : poppler-utils non installé.
   - Résolution : `sudo apt install poppler-utils`.

9. **Accès `/dev/ttyUSB0` refusé**
   - Cause : utilisateur hors groupe `dialout`.
   - Résolution : `sudo usermod -aG dialout moise` + reconnexion.

---

## Architecture logicielle envisagée

À terme (créer chaque module à son étape, ne rien créer artificiellement) :

```
project/
├── PROJECT_CONTEXT.md
├── SESSION_LOG.md
├── README.md
├── docs/
├── src/
│   ├── main.cpp
│   ├── motor.cpp / motor.h
│   ├── encoder.cpp / encoder.h
│   ├── imu.cpp / imu.h
│   ├── pid.cpp / pid.h
│   └── communication.cpp / communication.h
└── tests/
```

---

## Sécurité

Avant toute commande moteur :

- Toujours demander confirmation utilisateur.
- Vérifier l'alimentation ; roues libres / robot stable.
- Commencer faible (vitesse), durée courte.
- Prévoir un arrêt (forcé dans `finally`).

Ordre des diagnostics (jamais l'inverse) :

```
1. USB → 2. ttyUSB0 → 3. Communication série → 4. IMU
→ 5. Encodeurs → 6. PID → 7. Moteurs
```

---

## Dossiers importants

- Projet : `~/ROSMASTER-R2`
- Travail personnel : `~/Rosmaster`
- Lib source : `~/Rosmaster/py_install/Rosmaster_Lib/Rosmaster_Lib.py`

---

## Mission d'OpenCode

Toujours :

- expliquer les modifications ;
- préserver Git ;
- documenter les découvertes ;
- ne jamais supprimer des fichiers sans confirmation ;
- ne jamais modifier le réseau inutilement.

---

## Prochaines étapes

1. ✅ Environnement + lib + communication + tests moteurs (voir historique)
2. ✅ Propulsion M1+M3 validée sous 7,4 V (avant/recul, tout droit)
3. ✅ IMU temps réel ; carte reconfigurée R2 ; sonde PID OK
4. 🔲 **PID d'équilibre — finaliser**
   - 🔲 Rock doux pour affiner la cible (pitch ≈ −40/−47°)
   - 🔲 KP croissant → vrai lâché (pare-chocs / mains prêtes)
   - 🔲 Re-tester `set_car_motion` une fois debout
5. 🔲 PID vitesse / encodeur
6. 🔲 PID direction / rotation
7. 🔲 Contrôle complet (marche avant/arrière, arrêt)
8. 🔲 Fusion IMU + encodeurs → auto-équilibrage complet
9. 🔲 Mise en place de l'architecture `src/` + `tests/`

## Objectif final

```
PC
 ↓ SSH
Raspberry Pi 5
 ↓ USB / série
YAHBOOM YB-ERF01-V3.0
 ↓ contrôleur moteur
moteur gauche + moteur droit
 ↓ encodeurs
```

Puis :

```
IMU + encodeurs
 ↓ fusion
PID
 ↓ commande moteur
robot auto-équilibré
```

NE PAS SAUTER LES ÉTAPES.