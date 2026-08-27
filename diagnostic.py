#!/usr/bin/env python3
"""
ROSMASTER R2 — Script de diagnostic complet
Aucune commande moteur n'est envoyée.

Teste :
  1. Connexion série
  2. Firmware / version
  3. Batterie
  4. IMU (gyroscope, accéléromètre, attitude)
  5. Encodeurs
  6. Buzzer (court bip de 200ms)
  7. Vitesse du robot (get_motion_data)

Usage :
  python3 diagnostic.py
"""

import sys
import time

from Rosmaster_Lib import Rosmaster

PORT = "/dev/ttyUSB0"
CAR_TYPE = 5          # CARTYPE_R2 = 0x05
BAUDRATE = 115200
DURATION = 3.0        # secondes de lecture IMU/encodeurs
FREQ_HZ = 50          # fréquence d'affichage souhaitée (~20ms entre lectures)

def separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def main():
    robot = None
    try:
        # ----------------------------------------------------------
        # 1. CONNEXION
        # ----------------------------------------------------------
        separator("1. CONNEXION SERIE")
        print(f"Port   : {PORT}")
        print(f"Baud   : {BAUDRATE}")
        print(f"CarType: {CAR_TYPE} (R2)")

        robot = Rosmaster(car_type=CAR_TYPE, com=PORT, delay=0.002, debug=False)

        if not robot.ser.isOpen():
            print("[ERREUR] Port serie non ouvert !")
            sys.exit(1)

        print("[OK] Port serie ouvert.")

        # ----------------------------------------------------------
        # 2. THREAD RECEPTION
        # ----------------------------------------------------------
        separator("2. THREAD RECEPTION")
        robot.create_receive_threading()
        print("[OK] Thread de reception lance.")
        time.sleep(0.5)  # laisser le temps au premier paquet

        # ----------------------------------------------------------
        # 3. FIRMWARE / VERSION
        # ----------------------------------------------------------
        separator("3. FIRMWARE")
        version = robot.get_version()
        print(f"Version firmware : {version}")

        car_type_machine = robot.get_car_type_from_machine()
        print(f"Car type machine : {car_type_machine} (attendu: {CAR_TYPE})")

        # ----------------------------------------------------------
        # 4. BATTERIE
        # ----------------------------------------------------------
        separator("4. BATTERIE")
        voltage = robot.get_battery_voltage()
        print(f"Tension batterie : {voltage:.1f} V")
        if voltage < 6.0:
            print("[ATTENTION] Batterie tres faible !")
        elif voltage < 7.0:
            print("[ATTENTION] Batterie basse.")
        else:
            print("[OK] Batterie acceptable.")

        # ----------------------------------------------------------
        # 5. BUZZER (test court, 200ms)
        # ----------------------------------------------------------
        separator("5. BUZZER (200ms)")
        print("Bip court...")
        robot.set_beep(200)
        time.sleep(0.3)
        print("[OK] Buzzer teste.")

        # ----------------------------------------------------------
        # 6. IMU — lecture pendant DURATION secondes
        # ----------------------------------------------------------
        separator(f"6. IMU — lecture pendant {DURATION}s")
        robot.clear_auto_report_data()
        time.sleep(0.1)

        interval = 1.0 / FREQ_HZ
        t_start = time.time()
        imu_count = 0
        last_print = 0

        pitch_sum = 0.0
        pitch_min = 999.0
        pitch_max = -999.0

        while (time.time() - t_start) < DURATION:
            t_loop = time.time()

            gyro = robot.get_gyroscope_data()
            accel = robot.get_accelerometer_data()
            roll, pitch, yaw = robot.get_imu_attitude_data(ToAngle=True)

            pitch_sum += pitch
            if pitch < pitch_min:
                pitch_min = pitch
            if pitch > pitch_max:
                pitch_max = pitch
            imu_count += 1

            now = time.time() - t_start
            if now - last_print >= 0.5:
                last_print = now
                print(f"  t={now:5.2f}s | "
                      f"gyro=({gyro[0]:+7.3f}, {gyro[1]:+7.3f}, {gyro[2]:+7.3f}) | "
                      f"accel=({accel[0]:+7.3f}, {accel[1]:+7.3f}, {accel[2]:+7.3f}) | "
                      f"roll={roll:+7.2f} pitch={pitch:+7.2f} yaw={yaw:+7.2f}")

            elapsed = time.time() - t_loop
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        if imu_count > 0:
            pitch_avg = pitch_sum / imu_count
            print(f"\n  Resume IMU ({imu_count} echantillons) :")
            print(f"    pitch moyenne : {pitch_avg:+7.2f} deg")
            print(f"    pitch min     : {pitch_min:+7.2f} deg")
            print(f"    pitch max     : {pitch_max:+7.2f} deg")
            print(f"    amplitude     : {pitch_max - pitch_min:7.2f} deg")
            freq_actual = imu_count / DURATION
            print(f"    frequence     : {freq_actual:.1f} Hz")
            print(f"    [OK] IMU fonctionne.")
        else:
            print("  [ERREUR] Aucune donnee IMU recue !")

        # ----------------------------------------------------------
        # 7. ENCODEURS
        # ----------------------------------------------------------
        separator("7. ENCODEURS")
        m1, m2, m3, m4 = robot.get_motor_encoder()
        print(f"  M1 (haut gauche) : {m1}")
        print(f"  M2 (bas  gauche) : {m2}")
        print(f"  M3 (haut droit)  : {m3}")
        print(f"  M4 (bas  droit)  : {m4}")
        if m1 == 0 and m2 == 0 and m3 == 0 and m4 == 0:
            print("  [INFO] Tous les encodeurs a 0 — robot a l'arret, normal.")
        else:
            print("  [OK] Encodeurs lisent des valeurs non nulles.")

        # ----------------------------------------------------------
        # 8. VITESSE (motion data)
        # ----------------------------------------------------------
        separator("8. VITESSE (motion data)")
        vx, vy, vz = robot.get_motion_data()
        print(f"  vx (longitudinal) : {vx:+.4f} m/s")
        print(f"  vy (lateral)      : {vy:+.4f} m/s")
        print(f"  vz (rotation)     : {vz:+.4f} rad/s")
        if abs(vx) < 0.01 and abs(vy) < 0.01 and abs(vz) < 0.01:
            print("  [OK] Robot a l'arret.")
        else:
            print("  [INFO] Robot en mouvement ou donnees non zeroes.")

        # ----------------------------------------------------------
        # 9. PID MOTION
        # ----------------------------------------------------------
        separator("9. PID MOTION")
        pid = robot.get_motion_pid()
        print(f"  PID : kp={pid[0]:.3f}  ki={pid[1]:.3f}  kd={pid[2]:.3f}")
        if pid[0] == -1:
            print("  [ERREUR] Lecture PID echouee.")
        else:
            print("  [OK] PID lue.")

        # ----------------------------------------------------------
        # RESUME FINAL
        # ----------------------------------------------------------
        separator("RESUME DIAGNOSTIC")
        print(f"  Connexion      : OK")
        print(f"  Firmware       : V{version}")
        print(f"  Batterie       : {voltage:.1f} V")
        print(f"  IMU            : {imu_count} echantillons, pitch moy={pitch_avg:.2f} deg" if imu_count > 0 else "  IMU : ERREUR")
        print(f"  Encodeurs      : M1={m1} M2={m2} M3={m3} M4={m4}")
        print(f"  Vitesse        : vx={vx:.4f} vy={vy:.4f} vz={vz:.4f}")
        print(f"  PID            : kp={pid[0]:.3f} ki={pid[1]:.3f} kd={pid[2]:.3f}")
        print(f"\n  Aucune commande moteur envoyee.")
        print(f"  Diagnostic termine avec succes.")

    except KeyboardInterrupt:
        print("\n[ARRET] Ctrl+C — arret propre.")
    except Exception as e:
        print(f"\n[ERREUR] {type(e).__name__}: {e}")
    finally:
        if robot is not None:
            try:
                robot.set_beep(0)
            except:
                pass
            try:
                robot.ser.close()
                print("[OK] Port serie ferme.")
            except:
                pass


if __name__ == "__main__":
    main()
