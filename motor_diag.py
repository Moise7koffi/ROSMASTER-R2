#!/usr/bin/env python3
"""
ROSMaster R2 — Diagnostic moteur ciblé M1 / M3 (analyse du test precedent)

But : déterminer si
  - le moteur M3 (roue droite) fonctionne
  - le moteur M1 tourne de façon fiable
  - les encodeurs répondent

Chaque moteur est testé plusieurs fois, avec arrêt forcé entre chaque essai.
Vitesse 20/100, durée 1.0s (toujours faible et courte).
Aucune confirmation interactive -> pilotage DANS la conversation.
"""

import sys
import time

from Rosmaster_Lib import Rosmaster

PORT = "/dev/ttyUSB0"
CAR_TYPE = 5
SPEED = 20
DUR = 1.0


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


def spin(robot, label, s1, s2, s3, s4):
    sep(label)
    try:
        b = robot.get_motor_encoder()
        print(f"  avant : M1={b[0]} M2={b[1]} M3={b[2]} M4={b[3]}")
    except Exception:
        b = None
    time.sleep(0.2)
    try:
        robot.set_motor(s1, s2, s3, s4)
        print(f"  rotation {DUR}s...", flush=True)
        time.sleep(DUR)
    finally:
        stop(robot)
    time.sleep(0.2)
    try:
        if b:
            a = robot.get_motor_encoder()
            d = (a[0]-b[0], a[1]-b[1], a[2]-b[2], a[3]-b[3])
            print(f"  apres : M1={a[0]} M2={a[1]} M3={a[2]} M4={a[3]}")
            print(f"  delta : M1={d[0]:+d} M2={d[1]:+d} M3={d[2]:+d} M4={d[3]:+d}")
            return d
    except Exception as e:
        print(f"  [ERREUR] {e}")
    return None


def main():
    robot = None
    try:
        sep("CONNEXION")
        robot = Rosmaster(car_type=CAR_TYPE, com=PORT, delay=0.002, debug=False)
        if not robot.ser.isOpen():
            print("[ERREUR] port non ouvert")
            sys.exit(1)
        robot.create_receive_threading()
        time.sleep(0.3)

        vol = robot.get_battery_voltage()
        print(f"  Batterie : {vol:.1f} V")
        if vol < 6.0:
            print("[ABORT] batterie faible")
            sys.exit(1)

        spin(robot, "M1 (roue gauche) +20, 1.0s  —  essai A", SPEED, 0, 0, 0)
        spin(robot, "M3 (roue droite) +20, 1.0s  —  essai B", 0, 0, SPEED, 0)
        spin(robot, "M1 (roue gauche) +20, 1.0s  —  essai C", SPEED, 0, 0, 0)
        spin(robot, "M3 (roue droite) +20, 1.0s  —  essai D", 0, 0, SPEED, 0)

        sep("FIN")
        print("  Moteurs arretes.")
    except KeyboardInterrupt:
        print("\n[ARRET] Ctrl+C")
    except Exception as e:
        print(f"\n[ERREUR] {type(e).__name__}: {e}")
    finally:
        if robot is not None:
            try:
                stop(robot)
            except Exception:
                pass
            try:
                robot.ser.close()
                print("[OK] port ferme.")
            except Exception:
                pass


if __name__ == "__main__":
    main()
