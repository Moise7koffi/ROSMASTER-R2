#!/usr/bin/env python3
"""
ROSMaster R2 — Test propulsion 2 moteurs sous batterie 7.4 V (2S LiPo)

Batterie : 7.4 V nominal (2S LiPo) — le système vise DC 12 V.
  Consequence : ~38% de tension en moins → couple de démarrage réduit.
  Donc vitesse PWM de test plus elevee que sur 12 V (+20).

Moteurs testes (propulsion R2 uniquement) :
  M1 = haut gauche  -> roue gauche
  M3 = haut droit   -> roue droite
  M2 / M4 = IGNORES (non utilises sur R2 2-roues)

Sequence (chaque essai encadre d'un arret force) :
  1. M1 seul  +20, 1.0s  (roue gauche)
  2. M3 seul  +20, 1.0s  (roue droite)
  3. M1 + M3  +20, 1.0s  (avancer)
  4. M1 + M3  -20, 1.0s  (reculer — valide le sens)

Seuil batterie : 2S LiPo a ~3.3 V/cellule sous charge -> 6.6 V.
  - < 6.5 V : ABORT (trop faible, risque de comportement erratique)
  - 6.5-7.0 : ATTENTION (on peut continuer mais resultats a confirmer)

Securite :
  - Roues DEGAGEES du sol / robot stable
  - Duree courte (1.0s), vitesse bornee
  - Arret force dans finally
"""

import sys
import time

from Rosmaster_Lib import Rosmaster

PORT = "/dev/ttyUSB0"
CAR_TYPE = 5          # R2 (l'argument n'affecte que set_car_run/motion, pas set_motor)
SPEED_LO = 20         # vitesse 1 (roue seule)
SPEED_HI = 30         # vitesse 2 (augmentee si necessaire, sous confirmation)
DUR = 1.0
ABORT_VOLT = 6.5      # seuil 2S LiPo (~3.25 V/cellule) — en dessous, on ne tourne pas
WARN_VOLT = 7.0
MOTORS_INVOLVED = [0, 2]  # index 0=M1, 2=M3


def sep(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


def stop(robot):
    try:
        robot.set_motor(0, 0, 0, 0)
    except Exception:
        pass
    try:
        robot.set_car_run(0, 0)
    except Exception:
        pass


def spin(robot, label, s1, s2, s3, s4, dur=DUR):
    sep(label)
    try:
        b = robot.get_motor_encoder()
        print(f"  avant : M1={b[0]} M2={b[1]} M3={b[2]} M4={b[3]}")
    except Exception:
        b = None
    time.sleep(0.2)
    try:
        robot.set_motor(s1, s2, s3, s4)
        print(f"  >> rotation {dur}s...", flush=True)
        time.sleep(dur)
    finally:
        stop(robot)
    time.sleep(0.2)
    try:
        if b is not None:
            a = robot.get_motor_encoder()
            d = (a[0]-b[0], a[1]-b[1], a[2]-b[2], a[3]-b[3])
            print(f"  apres : M1={a[0]} M2={a[1]} M3={a[2]} M4={a[3]}")
            print(f"  delta : M1={d[0]:+d} M2={d[1]:+d} M3={d[2]:+d} M4={d[3]:+d}")
            involved = " | ".join(f"M{i+1}={d[i]:+d}" for i in MOTORS_INVOLVED)
            print(f"  >>>  {involved}   (seules les 2 roues comptent)")
            return d
    except Exception as e:
        print(f"  [ERREUR] {e}")
    return None


def check_battery(robot):
    vol = robot.get_battery_voltage()
    print(f"  Batterie : {vol:.2f} V  (nominal 7.4 V / 2S LiPo)")
    if vol < ABORT_VOLT:
        print(f"[ABORT] Batterie {vol:.2f} V < {ABORT_VOLT} V (2S LiPo presque vide).")
        print("        Aucun moteur actionne.")
        sys.exit(1)
    if vol < WARN_VOLT:
        print(f"[ATTENTION] {vol:.2f} V : sous charge, possible manque de couple "
              f"avec les 2 moteurs. Si un moteur ne tourne pas, a tester plus vite.")
    return vol


def main():
    robot = None
    try:
        sep("CONNEXION")
        robot = Rosmaster(car_type=CAR_TYPE, com=PORT, delay=0.002, debug=False)
        if not robot.ser.isOpen():
            print("[ERREUR] port non ouvert")
            sys.exit(1)
        print("[OK] port serie ouvert.")
        robot.create_receive_threading()
        time.sleep(0.5)

        vol = check_battery(robot)

        it = input(f"\nLancer la sequence de tests ? (batterie {vol:.2f} V, "
                   f"vitesse {SPEED_LO}, duree {DUR}s) [o/N]: ").strip().lower()
        if it not in ("o", "oui", "y", "yes"):
            print("Abandon : aucun moteur actionne.")
            sys.exit(0)

        spin(robot, "1. M1 seul (roue GAUCHE) +20", SPEED_LO, 0, 0, 0)
        spin(robot, "2. M3 seul (roue DROITE) +20", 0, 0, SPEED_LO, 0)
        spin(robot, "3. M1 + M3 (AVANCER) +20", SPEED_LO, 0, SPEED_LO, 0)
        spin(robot, "4. M1 + M3 (RECULER) -20", -SPEED_LO, 0, -SPEED_LO, 0)

        sep("BILAN")
        print("  Moteurs arretes.")
        print("  -> Comparez les deltas M1 et M3 a chaque etape.")
        print("  -> Les deux roues doivent bouger ensemble en 3 et 4.")
        print("  -> En 4 (reculer) les deltas doivent etre negatifs.")

    except KeyboardInterrupt:
        print("\n[ARRET] Ctrl+C — arret propre.")
    except Exception as e:
        print(f"\n[ERREUR] {type(e).__name__}: {e}")
    finally:
        if robot is not None:
            try:
                stop(robot)
                print("[OK] moteurs arretes (finally).")
            except Exception:
                pass
            try:
                robot.ser.close()
                print("[OK] port ferme.")
            except Exception:
                pass


if __name__ == "__main__":
    main()