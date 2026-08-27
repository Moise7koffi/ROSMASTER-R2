#!/usr/bin/env python3
"""
ROSMaster R2 — Test moteur PWM brut (version pilotée, SANS input interactif)

Différence avec motor_test.py :
  - Pas de input() : les séquences sont enchaînées automatiquement.
  - Sécurité renforcée : délais de prévenance + arrêt systématique.
  - Pilotage des confirmations assuré DANS LA CONVERSATION (OpenCode),
    pas via stdin.

SÉQUENCE (chaque étape est entourée d'un arrêt forcé):
  1. M1 seul (roue gauche)  : +10, 0.5s
  2. M3 seul (roue droite)  : +10, 0.5s
  3. M1 + M3 ensemble       : +10, 0.5s

Sécurité du pilotage :
  - La confirmation se fait par retour utilisateur NAME de la conversation.
  - Le script vérifie la batterie avant tout mouvement.
  - Chaque rotation est précédée de COUNTDOWN (3s) affiché à l'écran.
  - Arrêt forcé dans finally en toutes circonstances.
"""

import sys
import time

from Rosmaster_Lib import Rosmaster

PORT = "/dev/ttyUSB0"
CAR_TYPE = 5
BAUDRATE = 115200

DEFAULT_SPEED = 10
DEFAULT_DUR = 0.5
COUNTDOWN = 3


def separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def stop_all(robot):
    try:
        robot.set_motor(0, 0, 0, 0)
    except Exception as e:
        print(f"  [ERREUR arret set_motor] {e}")
    try:
        robot.set_car_run(0, 0)
    except Exception as e:
        print(f"  [ERREUR arret set_car_run] {e}")


def countdown(n):
    for i in range(n, 0, -1):
        print(f"    Rotation dans {i}s...", flush=True)
        time.sleep(1)


def do_spin(robot, label, s1, s2, s3, s4, dur):
    separator(f"TEST : {label}")
    print(f"  set_motor({s1}, {s2}, {s3}, {s4})  dur={dur}s")
    try:
        enc_before = robot.get_motor_encoder()
        print(f"  Encodeurs avant : M1={enc_before[0]} M2={enc_before[1]} "
              f"M3={enc_before[2]} M4={enc_before[3]}")
    except Exception as e:
        enc_before = None
        print(f"  [INFO] encodeur avant indisponible: {e}")

    print(f"  Démarrage automatique dans {COUNTDOWN}s...")
    countdown(COUNTDOWN)
    try:
        robot.set_motor(s1, s2, s3, s4)
        print(f"  >> Rotation {dur}s...", flush=True)
        time.sleep(dur)
    finally:
        stop_all(robot)
        print("  >> Arret force (tous moteurs coupes).")

    time.sleep(0.3)
    try:
        if enc_before:
            enc_after = robot.get_motor_encoder()
            print(f"  Encodeurs apres : M1={enc_after[0]} M2={enc_after[1]} "
                  f"M3={enc_after[2]} M4={enc_after[3]}")
            print(f"  Variation : M1={enc_after[0]-enc_before[0]:+d} "
                  f"M2={enc_after[1]-enc_before[1]:+d} "
                  f"M3={enc_after[2]-enc_before[2]:+d} "
                  f"M4={enc_after[3]-enc_before[3]:+d}")
    except Exception as e:
        print(f"  [INFO] encodeur apres indisponible: {e}")


def main():
    robot = None
    try:
        separator("CONNEXION")
        print(f"  Port   : {PORT}")
        print(f"  Baud   : {BAUDRATE}")
        print(f"  CarType: {CAR_TYPE} (R2)")

        robot = Rosmaster(car_type=CAR_TYPE, com=PORT, delay=0.002, debug=False)
        if not robot.ser.isOpen():
            print("[ERREUR] Port serie non ouvert !")
            sys.exit(1)
        print("[OK] Port serie ouvert.")

        robot.create_receive_threading()
        time.sleep(0.3)

        separator("INFO CARTE")
        version = robot.get_version()
        voltage = robot.get_battery_voltage()
        print(f"  Version firmware : {version}")
        print(f"  Batterie         : {voltage:.1f} V")
        if voltage < 6.0:
            print("[ABORT] Batterie trop faible — aucun moteur.")
            sys.exit(1)

        try:
            m1, m2, m3, m4 = robot.get_motor_encoder()
            print(f"  Encodeurs initiaux : M1={m1} M2={m2} M3={m3} M4={m4}")
        except Exception as e:
            print(f"  [INFO] encodeurs initiaux indisponible: {e}")

        do_spin(robot, "M1 seul (roue GAUCHE, +10)", DEFAULT_SPEED, 0, 0, 0, DEFAULT_DUR)
        do_spin(robot, "M3 seul (roue DROITE, +10)", 0, 0, DEFAULT_SPEED, 0, DEFAULT_DUR)
        do_spin(robot, "M1 + M3 ensemble (+10)", DEFAULT_SPEED, 0, DEFAULT_SPEED, 0, DEFAULT_DUR)

        separator("FIN DES TESTS")
        print("  Tous les moteurs sont arretes.")

    except KeyboardInterrupt:
        print("\n[ARRET] Ctrl+C — arret propre.")
    except Exception as e:
        print(f"\n[ERREUR] {type(e).__name__}: {e}")
    finally:
        if robot is not None:
            try:
                stop_all(robot)
                print("[OK] Moteurs arretes (finally).")
            except Exception as e:
                print(f"[ERREUR] arret finally : {e}")
            try:
                robot.ser.close()
                print("[OK] Port serie ferme.")
            except Exception as e:
                print(f"[ERREUR] fermeture port : {e}")


if __name__ == "__main__":
    main()
