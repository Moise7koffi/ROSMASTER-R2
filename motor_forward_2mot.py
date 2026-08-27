#!/usr/bin/env python3
"""
ROSMaster R2 — M1 + M3 EN AVANT, escalade de vitesse (sous 7.4 V)

Objectif : faire tourner les DEUX roues en avant (controle visuel).
Vitesses successives (1.0s chacune, arret force entre chaque) :
  +30 -> +45 -> +60
Permet de trouver le seuil de demarrage de chaque moteur a 7.4 V.

Si M1 (gauche) ne bouge toujours pas a +60 : connexion/cable M1 a inspecter.
"""

import sys
import time

from Rosmaster_Lib import Rosmaster

PORT = "/dev/ttyUSB0"
CAR_TYPE = 5
STEPS = [(30, 1.0), (45, 1.0), (60, 1.0)]
ABORT_VOLT = 6.5


def sep(t):
    print(f"\n{'='*60}\n  {t}\n{'='*60}")


def stop(robot):
    try:
        robot.set_motor(0, 0, 0, 0)
    except Exception:
        pass
    try:
        robot.set_car_run(0, 0)
    except Exception:
        pass


def forward(robot, speed, dur):
    sep(f"M1 + M3 EN AVANT  +{speed}  ({dur}s)")
    try:
        b = robot.get_motor_encoder()
        print(f"  avant : M1={b[0]} M3={b[2]}")
    except Exception:
        b = None
    time.sleep(0.2)
    try:
        robot.set_motor(speed, 0, speed, 0)   # M1 + M3 positifs = avant
        print(f"  >> rot +{speed} pendant {dur}s...", flush=True)
        time.sleep(dur)
    finally:
        stop(robot)
    time.sleep(0.2)
    try:
        a = robot.get_motor_encoder()
        print(f"  apres : M1={a[0]} M3={a[2]}")
        if b is not None:
            print(f"  delta : M1={a[0]-b[0]:+d}  M3={a[2]-b[2]:+d}")
    except Exception as e:
        print(f"  [ERREUR] {e}")


def main():
    robot = None
    try:
        sep("CONNEXION")
        robot = Rosmaster(car_type=CAR_TYPE, com=PORT, delay=0.002, debug=False)
        if not robot.ser.isOpen():
            print("[ERREUR] port non ouvert")
            sys.exit(1)
        robot.create_receive_threading()
        time.sleep(0.5)

        vol = robot.get_battery_voltage()
        print(f"  Batterie : {vol:.2f} V")
        if vol < ABORT_VOLT:
            print("[ABORT] batterie trop faible.")
            sys.exit(1)

        for speed, dur in STEPS:
            forward(robot, speed, dur)
            time.sleep(0.3)

        sep("BILAN")
        print("  Attendu : les 2 roues avancent ; M3 (droite) a confirmer en visuel.")
    except KeyboardInterrupt:
        print("\n[ARRET] Ctrl+C")
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
            except Exception:
                pass


if __name__ == "__main__":
    main()