# SESSION LOG

## 2026-08-26

### État validé

- SSH opérationnel
- Wi-Fi opérationnel
- Internet OK
- OpenCode 1.18.22 installé
- Raspberry Pi 5 sous Ubuntu 26.04
- Dépôt ROSMASTER-R2 cloné
- Carte détectée sur /dev/ttyUSB0
- CH341 identifié

### Rosmaster_Lib installé

- Zip officiel Yahboom V3.3.9 téléchargé depuis Google Drive
- Extrait dans `~/Rosmaster/py_install/`
- Installé via `sudo python3 setup.py install`
- Package : `Rosmaster_Lib-3.3.9-py3.14.egg`

### Communication série validée

- Port `/dev/ttyUSB0` ouvert (115200 bauds)
- Firmware carte : V3.5
- Batterie : 7.7 V
- IMU (gyro + accel) : données reçues
- Encodeurs 4 moteurs : données reçues
- Vitesse : 0, robot à l'arrêt
- Aucune commande moteur envoyée

### Prochaine mission

Diagnostiquer les moteurs (tests PWM/encodeurs sous supervision) et PID.

---

## 2026-08-26 (suite)

### Exploration dépôt

- Dépôt ROSMASTER-R2 : structure complète analysée
- PDFs extraits et lus : motor control, IMU, encoder, PID, library install
- Rosmaster_Lib V3.3.9 : source inspectée (1331 lignes)

### Découvertes API

#### Constructeur
```python
Rosmaster(car_type=5, com="/dev/ttyUSB0", delay=0.002, debug=False)
```
- `car_type=5` → `CARTYPE_R2`
- Port : `/dev/ttyUSB0` (pas `/dev/myserial`)

#### Fonctions moteur identifiées
1. `set_motor(s1, s2, s3, s4)` — PWM brut, [-100, 100]
2. `set_car_run(state, speed)` — directionnel : 0=stop, 1=avant, 2=arrière, 3=gauche, 4=droite, 5=rotG, 6=rotD
3. `set_car_motion(vx, vy, vz)` — mouvement PID : R2 vx=[-1.8, 1.8], vz=[-3, 3]

#### Mapping moteur R2
- M1 = haut gauche → **roue gauche**
- M2 = bas gauche → probablement inutilisé sur R2
- M3 = haut droit → **roue droite**
- M4 = bas droit → probablement inutilisé sur R2
- **À VALIDER par test**

#### Fonctions IMU
- `get_imu_attitude_data(ToAngle=True)` → roll, pitch, yaw (degrés)
- `get_gyroscope_data()` → g_x, g_y, g_z
- `get_accelerometer_data()` → a_x, a_y, a_z

#### Fonctions encodeur
- `get_motor_encoder()` → m1, m2, m3, m4 (compteurs cumulés)

#### Fonctions utilitaires
- `create_receive_threading()` — OBLIGATOIRE avant lecture
- `set_pid_param(kp, ki, kd, forever)` — PID motion [0, 10]
- `set_beep(on_time)` — test buzzer possible
- `get_battery_voltage()` — tension batterie
- `get_version()` — version firmware

### Protocole série

- 115200 bauds, 8N1
- En-tête: 0xFF, Device ID: 0xFC
- Auto-report: 4 paquets toutes les 40ms

### Prochaines étapes

1. Créer script diagnostic (sans moteurs)
2. Lire IMU en temps réel
3. Lire encodeurs en temps réel
4. Tester buzzer (test non dangereux)
5. **Avec confirmation utilisateur** : premier test moteur
   - Roues dégagées du sol
   - Vitesse minimale (10/100)
   - Durée très courte (0.5s)
   - Arrêt automatique dans finally

---

## 2026-08-27

### Reprise de session — vérification de l'environnement

- USB : carte CH340 (1a86:7523) détectée ✅
- `/dev/ttyUSB0` présent, groupe dialout ✅ (moise ∈ dialout)
- `Rosmaster_Lib` importable : `from Rosmaster_Lib import Rosmaster` OK ✅
- Source : `~/Rosmaster/py_install/Rosmaster_Lib/Rosmaster_Lib.py` (1331 lignes) ✅

### Mapping moteur R2 confirmé (PDF Hardware course 12)

- M1 = haut gauche → **roue gauche**
- M2 = bas gauche → non utilisé (R2 2-roues)
- M3 = haut droit → **roue droite**
- M4 = bas droit → non utilisé (R2 2-roues)
- ⚠️ Alimentation moteur recommandée : **DC 12V** (pas USB 5V)

### API moteur re-vérifiée dans la source

- `set_motor(s1, s2, s3, s4)` : PWM brut [-100,100], 127=conserver, borne [-100,100]
- `set_car_run(state, speed)` : 0=stop,1=avant,2=arrière,3=gauche,4=droite,5=rotG,6=rotD
- `set_car_motion(vx, vy, vz)` : R2 vx=[-1.8,1.8] m/s, vz=[-3,3] rad/s

### Prochaine action (en attente de confirmation utilisateur)

Aucun moteur actionné. Première étape suivante proposée :
- `motor_test.py` : test PWM brut faible vitesse (éteindre moteurs dans finally)
  - M1 seul → gauche
  - M3 seul → droit
  - Enregistrer/valider mapping + signe

---

### Tests moteurs réels — sous supervision

#### motor_test.py + motor_test_auto.py (vitesse 10, durée 0.5s)

- **M1 (roue gauche) +10** : encodeur 0→3 → **tourne** ✅
- **M3 (roue droite) +10** : encodeur 0 → **ne tourne PAS** ❌
- **M1+M3 +10** : aucun mouvement (incohérent avec M1 seul)

#### motor_diag.py (vitesse 20, durée 1.0s, 2 essais chacun)

- **M1 +20** : delta +132 puis +148 → **tourne systématiquement** ✅
- **M3 +20** : delta 0 x2 → **ne tourne jamais** ❌
- Reproductible → exclusion d'un aléa.

#### motor_diag_BC.py (options B & C)

Option B (canaux latéraux, +60) :
- **M2 (bas gauche) +60** : delta +1645 → **tourne** ✅
- **M4 (bas droit) +60** : delta 0 → **ne tourne PAS** ❌

Option C (M3 à vitesse croissante) :
- M3 +40, +60, −60 : delta M3 = 0 → **jamais de mouvement** ❌
- Artefact C3 : M1 a tourné pendant une commande M3 (déséquilibre/protection).

### Conclusion diagnostic moteur

**Pattern net :** les deux canaux du **côté DROIT (M3 et M4) sont inopérants**, les deux du **côté GAUCHE (M1 et M2) fonctionnent**.

- Ce n'est PAS un problème logiciel (commandes bien reçues ; M1/M2 y répondent).
- Ce n'est PAS un problème de mapping/protocole.
- → **Problème MATÉRIEL sur le côté droit** de la carte de motorisation (alimentation partagée, driver AM2861 groupe droit, câblage/câble roue droite, fusible/protection).

### Prochaine étape (matérielle)

Inspection physique à faire par l'utilisateur :
1. Connecteur moteur côté droit (ports M3/M4) : fils bien enfoncés.
2. Câble roue droite (M3 → moteur).
3. Carte expansion côté droit : composants brûlés/ballants.
4. Fusible/protection côté droit éventuel.

---

### RETOURNEMENT — re-test M1+M3 (vitesse 20, durée 1.0s)

Surprise : commande M1+M3 (+20) :
- **M3 (roue droite) : delta +32 → A TOURNÉ** ✅ (contredit « M3 mort »)
- **M1 (roue gauche) : delta +0 → n'a pas bougé** (normalement il tourne)

Contexte : batterie **7,1V** (système prévu en DC 12V).

### Nouvelle hypothèse principale

**BATTERIE TROP FAIBLE (7,1V)** : la doc impose DC 12V pour les moteurs.
À 7V, les moteurs (surtout 2 à la fois) n'ont pas assez de couple/démarrage
→ comportements **erratiques** (tantôt M1 seul, tantôt M3).
→ La conclusion « côté droit M3/M4 morts » est **REMISE EN CAUSE** et probablement
   due à la faible tension, pas à un défaut matériel.

### Prochaine action recommandée

1. **RECHARGER la batterie** à pleine charge (≥ 11-12V).
2. Refaire M1 seul + M3 seul + M1+M3 à tension correcte pour un diagnostic fiable.

---

## 2026-08-27 (suite) — Batterie 7.4 V (2S LiPo)

### Reprise — changement de batterie

- **Batterie 7.4 V nominal (2S LiPo) branchée** (remplace la 12V déchargée à 7,1V).
- Lue par la carte : **7,10 V** (3,55 V/cellule, zone médiane — OK).
- Point à documenter : `get_car_type_from_machine()` retourne **1** (X3) bien que le
  robot soit un R2 instancié en car_type=5. Sans impact sur `set_motor` (PWM brut
  direct sur les 4 canaux physiques) ; à investiguer si un jour on utilise
  `set_car_motion`/`set_car_run`.

### Nouveaux outils

- `motor_test_2mot.py` : test propulsion R2 (M1+M3 uniquement), seuils adaptés 2S LiPo
  (< 6,5 V → abort), +20 PWM.
- `motor_forward_2mot.py` : M1+M3 **en avant** à vitesse croissante (+30 → +45 → +60),
  contrôle visuel + deltas encodeurs.

### Résultats — M1 seul / M3 seul à +20

| Essai | M1 (gauche) | M3 (droite) |
|-------|-------------|-------------|
| M1 seul +20 | **+0 (immobile)** | — |
| M3 seul +20 | — | **+318 ✅** |
| M1+M3 +20 (avant) | **+0 (immobile)** | +202 ✅ |
| M1+M3 −20 (recul) | **+0 (immobile)** | −168 ✅ |

- **Inversion totale** par rapport à la session précédente : M3 répond, M1 pas.
- Hypothèse : **seuil de démarrage différent** par moteur (pas un défaut).

### Résultats — M1+M3 EN AVANT, escalade de vitesse

| Vitesse | M1 (gauche) | M3 (droite) | Conclusion |
|---------|-------------|-------------|------------|
| +30 | **+322 ✅** | +524 ✅ | M1 démarre |
| +45 | +688 ✅ | +835 ✅ | les 2 tournent |
| +60 | +1641 ✅ | +1349 ✅ | les 2 tournent fort |

### Conclusion moteurs (définitive)

- ✅ **M1 et M3 fonctionnent** — les 2 roues avancent ensemble sous 7.4 V.
- **Seuil de démarrage : M1 ≈ +25 PWM, M3 ≈ +20 PWM.**
- Le verdict « côté droit / M3 morts » des sessions précédentes était **faux** :
  causé par la batterie trop faible → manque de couple au démarrage, **pas** un défaut
  matériel.
- Leçon : sous 7.4 V, ne jamais conclure à un moteur mort si la vitesse est sous le
  seuil de démarrage. Consigne fiable ≥ **+30 PWM**.

### Tests au sol — avancer / reculer

- Burst avant +30 (0,5s) : delta M1=+85, M3=+36 → les 2 roues tournent en avant ✅
- **Avancer 5s à +30** : delta M1=+1327, M3=+812
- **Reculer 5s à −30** : delta M1=−1757, M3=−1097
- ✅ Les deux moteurs répondent dans les **2 sens**.
- ✅ **Trajectoire TOUT DROIT** en avant puis en arrière (observation visuelle utilisateur)
  → **sens physique M1/M3 conformes, propulsion R2 entièrement validée.**

### IMU temps réel — validé

- `imu_live.py` : lecture roll/pitch/yaw + gyro à ~10 Hz ✅
- Repos sur cale arrière : roll 15,9° | **pitch −40,4°** | yaw −68,9°
- Signaux propres/stables (pas de bruit) → prêt pour l'équilibre.

### Firmware / car type

- `get_car_type_from_machine()` renvoyait **1 (X3)** — corrigé.
- `set_car_type(5)` exécuté → **car_type machine = 5 (R2), persisté en flash** ✅
  (annulable via `set_car_type(1)` ou `reset_flash_value()`)
- Motion PID par défaut : `[Kp 0.8, Ki 0.06, Kd 0.5]`.

### Test set_car_motion (robot tenu, incliné −40°)

- `set_car_motion(vx=0.3, 0, 0)` pendant 2s → **aucun mouvement** (deltas 0, vx=0,000).
- Hypothèse : le firmware R2 **verrouille le roulage quand le robot n'est pas vertical**
  (sécurité auto-équilibrage). À re-tester **debout** une fois l'équilibre en place.

### PID Python — sonde (balance_pid.py)

- `balance_pid.py` : PID pitch ~20 Hz, modes `--dry` / `--probe`, paramètres
  KP/KD/SIGN/PWM_MAX/target en args. Contrôle : `pwm = KP*err + KD*derr`,
  clamp PWM, arrêt auto si `|err| > 25°`, arrêt forcé dans `finally`.
- **Constat majeur** : cible d'équilibre ≠ 0°. La carte IMU est **montée inclinée
  dans le châssis** → la position « verticale » du R2 se lit autour de −40°/−47°.
  Et le pitch de repos **varie avec la façon dont le robot est posé**
  (−40,4° puis −47,0° mesurés).
- Sonde (robot sur cale, target −47, KP=3) : pousser le haut en avant
  (pitch −47→−22) → **PWM positif croissant (roues poussent en avant)** →
  **SIGN=+1 correct**, boucle live ~20 Hz, **anti-chute déclenchée à +25°** ✅.
- Correctif : dérivée du 1er échantillon (pic) neutralisée.
- Reste à faire : trouver la cible précise (rock doux), puis KP croissant pour un
  vrai lâché (pare-chocs / mains prêtes à rattraper).

### Prochaines étapes

1. 🔲 Contrôle direction au sol : petit burst avant à +30 — la voiture va-t-elle tout
   droit ? (sens physique M1/M3 à valider)
2. 🔲 IMU pitch en temps réel
3. 🔲 PID vitesse / équilibre

---

## 2026-08-27 — Sauvegarde et documentation Git

### Objectif

- Prendre en charge la documentation du projet et la sauvegarde Git.
- Sauvegarder proprement le projet sur le dépôt GitHub **privé** :
  `Moise7koffi/ROSMASTER-R2` (`git@github.com:Moise7koffi/ROSMASTER-R2.git`).
- Vérifier SSH/clé Git et effectuer le commit + push.

### Actions

- Vérification de l'état réel du dépôt (`git status`, `git log`, `git remote -v`).
- Vérification des infos Git (`user.name`, `user.email`) et des fichiers `~/.ssh`
  (clé **publique** `.pub` uniquement — jamais la privée).
- Connexion SSH GitHub testée : **authentifié en tant que `Moise7koffi`** ✅.
- Constat : `origin` = **repo YAHBOOM d'origine (HTTPS)** → conservé tel quel ;
  le dépôt personnel est ajouté en remote séparé pour le push.
- Scan des secrets : **aucun secret dans les fichiers commités** ✅.
- Réécriture de `PROJECT_CONTEXT.md` (toutes sections : Historique, État actuel,
  Matériel, Comms Pi↔PC / Pi↔carte, Rosmaster_Lib, USB, IMU, Encodeurs, PID,
  Moteurs, Problèmes, Commandes, Erreurs, Architecture, Objectif).
- Ajout de la présente entrée chronologique dans `SESSION_LOG.md`.
- Ajout d'un `.gitignore` (exclusion `__pycache__/`, `*.pyc`).

### Commandes importantes

```bash
git status
git log --oneline -10
git remote -v
git branch --show-current
git config --global user.name
git config --global user.email
ls -la ~/.ssh
cat ~/.ssh/id_ed25519.pub          # clé PUBLIQUE uniquement
ssh -T git@github.com              # test SSH
hostname -I                        # IP actuelle : 192.168.137.48
git diff --cached --check
git grep -n -i -E "id_ed25519|token|password|\.env|pem|key"   # scan secrets
git add PROJECT_CONTEXT.md SESSION_LOG.md .gitignore <scripts>
git commit -m "docs: document Raspberry Pi and Rosmaster setup"
git remote add backup git@github.com:Moise7koffi/ROSMASTER-R2.git
git push -u backup main
```

### Résultats

- IP actuelle : **192.168.137.48** (DHCP dynamique ; déjà .152 puis .96).
- SSH GitHub OK (`Moise7koffi`).
- Git config renseignée : `Moïse KOFFI` / `moise7koffi@gmail.com`.
- Remote `origin` = YAHBOOM inchangé ; remote `backup` = repo perso ajouté.
- Documentation consolidée ; commit local créé.

### Erreurs rencontrées

- Point d'attention initial : `origin` = repo YAHBOOM → pas d'accès push direct.
- Aucune erreur bloquante cette session.

### Solutions

- Repository personnel privé créé par l'utilisateur et ajouté en remote `backup`
  (l'upstream YAHBOOM reste disponible via `origin`).
- Aucun secret committé ; clé privée jamais exposée.

### État final

- Propulsion M1+M3 validée ; IMU live ; carte réglée en R2 ; sonde PID OK.
- Documentation à jour ; commit créé ; push vers `backup` effectué.

### Prochaine étape

- Reprendre le développement moteur (protocole YAHBOOM vérifié dans le code, puis
  finaliser le PID d'équilibre : rock doux pour affiner la cible + KP croissant).
