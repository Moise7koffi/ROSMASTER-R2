#!/usr/bin/env python3
"""
ROSMaster R2 — Lecture IMU temps reel (roll, pitch, yaw)

Affiche l'attitude ~10Hz pendant N secondes.
Le PLUS IMPORTANT pour le R2 : l'axe PITCH (inclinaison avant/arriere).
Tilt: + = vers l'avant, - = vers l'arriere (a verifier).
"""

import sys
import time

from Rosmaster_Lib import Rosmaster

PORT = "/dev/ttyUSB0"
DUR = 10.0


def main():
    robot = None
    try:
        robot = Rosmaster(car_type=5, com=PORT, delay=0.002, debug=False)
        if not robot.ser.isOpen():
            print("[ERREUR] port non ouvert")
            sys.exit(1)
        robot.create_receive_threading()
        time.sleep(0.5)

        print(f"Lecture IMU pendant {DUR:.0f}s — penche doucement le robot "
              f"avant/arriere.\n")
        print(f"{'roll':>8} {'pitch':>8} {'yaw':>8}   gyroZ")
        t0 = time.time()
        while time.time() - t0 < DUR:
            roll, pitch, yaw = robot.get_imu_attitude_data()
            gx, gy, gz = robot.get_gyroscope_data()
            print(f"{roll:8.2f} {pitch:8.2f} {yaw:8.2f}   {gz:8.3f}",
                  flush=True)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n[ARRET] Ctrl+C")
    except Exception as e:
        print(f"\n[ERREUR] {type(e).__name__}: {e}")
    finally:
        if robot is not None:
            try:
                robot.ser.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()