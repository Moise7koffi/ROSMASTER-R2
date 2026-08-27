#!/usr/bin/env python3
"""
ROSMaster R2 — PID d'auto-equilibrage (Python, ~20 Hz)

Deux modes :
  --dry    : calibre le pitch vertical (moyenne, SANS moteur). Tenir le robot
             DEBOUT a la verticale pendant la mesure.
  (defaut) : boucle PID en moteur. Robot tenu vertical au demarrage, puis
             lache doucement. Arret auto si bascule / delai / Ctrl+C.

Loi : pwm = KP * (pitch - target) + KD * (dpitch/dt)
  pwm positif = roues en avant (sous le corps). Signe a inverser (SIGN)
  si le robot s'enfuit dans le mauvais sens.

Securite :
  - Clamp PWM a PWM_MAX
  - Anti-chute : |pitch - target| > FALL_DEG -> arret immediat
  - Arret force dans finally
  - Sous batterie 7.4 V : seuil demarrage moteur ~25 PWM (sans effet en loi
    continue, le PID pousse deja au-dessus a la moindre inclinaison)
"""

import argparse
import sys
import time

from Rosmaster_Lib import Rosmaster

PORT = "/dev/ttyUSB0"
CAR_TYPE = 5

KP = 3.0          # gain proportionnel conservateur pour la 1re sonde
KD = 0.3          # gain derive
SIGN = 1          # signe de correction (1 ou -1) — a valider par la sonde
PWM_MAX = 60.0    # saturation basse pour eviter tout saut (sous 7.4 V)
FALL_DEG = 25.0   # bascule toleree avant arret
DT_TARGET = 0.05  # periode boucle (~20 Hz)
MAX_RUN = 20.0    # duree max autorisee (s)
CAL_SAMPLES = 60  # echantillons pour le calibrage

# Constat 2026-08-27 : la carte IMU est montee INCLINEE dans le chassis R2.
# Attention : le pitch de REPOS varie avec la pose du robot (-40 a -47 selon
# l'appui). La cible par defaut est une ESTIMATION ; a affiner via la sonde.
TARGET_DEFAULT = -40.0


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def stop(robot):
    try:
        robot.set_motor(0, 0, 0, 0)
    except Exception:
        pass
    try:
        robot.set_car_run(0, 0)
    except Exception:
        pass


def calibrate(robot):
    print("Calibrage : tiens le robot DEBOUT a la verticale, ne bouge plus.\n")
    print("Calibrage dans 2s...")
    time.sleep(2)
    vals = []
    for i in range(CAL_SAMPLES):
        roll, pitch, yaw = robot.get_imu_attitude_data()
        vals.append(pitch)
        time.sleep(0.05)
    target = sum(vals) / len(vals)
    spread = max(vals) - min(vals)
    print(f"\npitch etalonnage : min={min(vals):.2f} max={max(vals):.2f} "
          f"moy={target:.2f}")
    if spread > 4.0:
        print("[AVERTISSEMENT] grand ecart pendant le calibrage, refais-le.")
    return target


def loop(robot, target):
    t_prev = time.time()
    pitch_prev = None
    t0 = time.time()
    print(f"\n>> EQUILIBRE ARME (KP={KP} KD={KD}) — "
          f"PWM_MAX={PWM_MAX} target={target:.2f}")
    print("   Lache le robot doucement. Ctrl+C pour arreter.\n")
    while time.time() - t0 < MAX_RUN:
        roll, pitch, yaw = robot.get_imu_attitude_data()
        now = time.time()
        dt = now - t_prev
        dt = max(dt, 0.001)
        err = pitch - target
        if pitch_prev is None:
            derr = 0.0
        else:
            derr = (pitch - pitch_prev) / dt

        pwm = SIGN * (KP * err + KD * derr)
        pwm = clamp(pwm, -PWM_MAX, PWM_MAX)
        p1 = int(pwm)
        p3 = int(pwm)

        robot.set_motor(p1, 0, p3, 0)

        if abs(err) > FALL_DEG:
            print(f"!! CHUTE (err={err:+.1f}°) — arret.")
            break

        print(f"pitch={pitch:7.2f}  err={err:+7.2f}  derr={derr:+7.2f}  "
              f"pwm={pwm:+6.1f}", flush=True)

        pitch_prev = pitch
        t_prev = now
        sleep_t = DT_TARGET - (time.time() - now)
        if sleep_t > 0:
            time.sleep(sleep_t)


def main():
    global KP, KD, SIGN, PWM_MAX, MAX_RUN
    ap = argparse.ArgumentParser(description="PID equilibrage R2")
    ap.add_argument("--dry", action="store_true",
                    help="calibrage sans moteur (tiens le robot debout)")
    ap.add_argument("--probe", action="store_true",
                    help="SONDE : robot pose sur sa cale, PWM faible, tu pousses "
                         "le haut du robot pour verifier le signe")
    ap.add_argument("--kp", type=float, default=KP)
    ap.add_argument("--kd", type=float, default=KD)
    ap.add_argument("--target", type=float, default=TARGET_DEFAULT,
                    help="pitch cible (defaut -40, position de repos)")
    ap.add_argument("--sign", type=int, default=SIGN)
    ap.add_argument("--max", type=float, default=PWM_MAX)
    ap.add_argument("--run", type=float, default=MAX_RUN)
    args = ap.parse_args()

    KP, KD, SIGN, PWM_MAX, MAX_RUN = (args.kp, args.kd, args.sign,
                                      args.max, args.run)

    robot = None
    try:
        robot = Rosmaster(car_type=CAR_TYPE, com=PORT, delay=0.0, debug=False)
        if not robot.ser.isOpen():
            print("[ERREUR] port non ouvert")
            sys.exit(1)
        robot.create_receive_threading()
        time.sleep(0.5)
        print(f"Batterie : {robot.get_battery_voltage():.2f} V")

        if args.probe:
            print(f"[PROBE] cible={args.target} KP={KP} KD={KD} "
                  f"SIGN={SIGN} PWM_MAX={PWM_MAX}")
            print("  Robot pose sur sa cale. Pousse le haut du robot")
            print("  DOUCEMENT vers l'avant, puis vers l'arriere.\n")
            loop(robot, args.target)
            return

        target = calibrate(robot)

        if args.dry:
            print("[DRY] Aucun moteur actionne. C'est tout.")
            return

        loop(robot, target)

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