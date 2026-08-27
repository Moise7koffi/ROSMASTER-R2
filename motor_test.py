#!/usr/bin/env python3
"""
ROSMaster R2 — Test moteur PWM brut (premier test)

OBJECTIF (validation progressive) :
  1. M1 seul (roue gauche) : faible vitesse, courte durée, arrêt
  2. M3 seul (roue droite) : faible vitesse, courte durée, arrêt
  3. (Optionnel) M1 + M3 ensemble

SÉCURITÉ :
  - Roues DÉGAGÉES du sol / robot posé stable
  - Alimentation moteur DC 12V branchée
  - Vitesse faible (DEFAULT_SPEED)
  - Durée courte (DEFAULT_DUR)
  - Arrêt FORCÉ dans finally quel que soit le résultat

AUCUN test ne démarre sans confirmation interactive de l'utilisateur.
"""

import sys
import time

from Rosmaster_Lib import Rosmaster

PORT = "/dev/ttyUSB0"
CAR_TYPE = 5          # CARTYPE_R2 = 0x05
BAUDRATE = 115200

DEFAULT_SPEED = 10    # vitesse faible sur [-100, 100]
DEFAULT_DUR = 0.5     # durée courte en secondes
STOP_SPEED = 0        # vitesse d'arrêt

# Mapping physique confirmé (PDF Hardware course 12)
# M1 = haut gauche  -> roue gauche
# M3 = haut droit   -> roue droite
# M2 / M4 = non utilisés sur R2 2-roues


def separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def ask_confirm(prompt):
    """Demande une confirmation explicite oui/non."""
    while True:
        ans = input(f"{prompt} [o/N]: ").strip().lower()
        if ans in ("o", "oui", "y", "yes"):
            return True
        if ans in ("", "n", "non", "no"):
            return False
        print("  Veuillez repondre par oui (o) ou non (n).")


def stop_all(robot):
    """Arrêt forcé : coupe les 4 moteurs + etat stop."""
    try:
        robot.set_motor(STOP_SPEED, STOP_SPEED, STOP_SPEED, STOP_SPEED)
    except Exception as e:
        print(f"  [ERREUR arret set_motor] {e}")
    try:
        robot.set_car_run(0, 0)   # state=0 => stop
    except Exception as e:
        print(f"  [ERREUR arret set_car_run] {e}")


def run_motor(robot, name, s1, s2, s3, s4, speed, dur, use_encoder=False):
    separator(f"TEST : {name}")
    print(f"  set_motor({s1}, {s2}, {s3}, {s4})  speed={speed}  dur={dur}s")
    if not ask_confirm("  Lancer ce test moteur ?"):
        print("  Test annule par l'utilisateur.")
        return None

    enc_before = None
    if use_encoder:
        try:
            enc_before = robot.get_motor_encoder()
            print(f"  Encodeurs avant : M1={enc_before[0]} M2={enc_before[1]} "
                  f"M3={enc_before[2]} M4={enc_before[3]}")
        except Exception as e:
            print(f"  [INFO] Lecture encodeur avant non dispo : {e}")

    try:
        # Vitesse
        robot.set_motor(s1, s2, s3, s4)
        print(f"  >> Rotation {name} pendant {dur}s ...")
        time.sleep(dur)
    finally:
        # Arrêt FORCÉ, quoi qu'il arrive
        stop_all(robot)
        print("  >> Arret force (tous moteurs coupés).")

    # Relecture encodeur après
    if use_encoder:
        try:
            enc_after = robot.get_motor_encoder()
            print(f"  Encodeurs apres : "
                  f"M1={enc_after[0]} M2={enc_after[1]} M3={enc_after[2]} M4={enc_after[3]}")
            if enc_before:
                print(f"  Variation : "
                      f"M1={enc_after[0]-enc_before[0]:+d} "
                      f"M2={enc_after[1]-enc_before[1]:+d} "
                      f"M3={enc_after[2]-enc_before[2]:+d} "
                      f"M4={enc_after[3]-enc_before[3]:+d}")
        except Exception as e:
            print(f"  [INFO] Lecture encodeur apres non dispo : {e}")

    return True


def main():
    robot = None
    try:
        separator("CONNEXION")
        print(f"  Port   : {PORT}")
        print(f"  Baud   : {BAUDRATE}")
        print(f"  CarType: {CAR_TYPE} (R2)")
        print("\n  AVERTISSEMENT :")
        print("  - Les roues/moteurs doivent etre DEGAGES du sol.")
        print("  - Alimentation moteur DC 12V branchée.")
        print("  - Aucun objet a proximité des roues.\n")

        if not ask_confirm("  Confirmer que la zone est sûre et prête ?"):
            print("  Abandon : zone non confirmée. Aucun moteur actionné.")
            sys.exit(0)

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
            print("  [ATTENTION] Batterie tres faible — ne pas lancer les moteurs !")
            sys.exit(1)

        # État initial encodeurs
        try:
            m1, m2, m3, m4 = robot.get_motor_encoder()
            print(f"  Encodeurs initiaux : M1={m1} M2={m2} M3={m3} M4={m4}")
        except Exception as e:
            print(f"  [INFO] Encodeurs initiaux non dispo : {e}")

        # ------------------------------------------------------------------
        # TEST 1 : Moteur gauche (M1) — roue gauche
        # ------------------------------------------------------------------
        sep = input("\nPrêt pour TEST 1 (roue gauche M1) ? [Entrée pour continuer / q pour quitter]: ")
        if sep.strip().lower() == "q":
            print("Abandon.")
            sys.exit(0)

        run_motor(robot, "M1 seul (roue GAUCHE, positif)", DEFAULT_SPEED, 0, 0, 0,
                  DEFAULT_SPEED, DEFAULT_DUR, use_encoder=True)
        time.sleep(0.3)

        # ------------------------------------------------------------------
        # TEST 2 : Moteur droit (M3) — roue droite
        # ------------------------------------------------------------------
        sep = input("\nPrêt pour TEST 2 (roue droite M3) ? [Entrée pour continuer / q pour quitter]: ")
        if sep.strip().lower() == "q":
            print("Abandon.")
            sys.exit(0)

        run_motor(robot, "M3 seul (roue DROITE, positif)", 0, 0, DEFAULT_SPEED, 0,
                  DEFAULT_SPEED, DEFAULT_DUR, use_encoder=True)
        time.sleep(0.3)

        # ------------------------------------------------------------------
        # TEST 3 (optionnel) : M1 + M3 ensemble
        # ------------------------------------------------------------------
        sep = input("\nPrêt pour TEST 3 (M1 + M3 ensemble, positif) ? [Entrée / q]: ")
        if sep.strip().lower() == "q":
            print("Abandon.")
            sys.exit(0)

        run_motor(robot, "M1 + M3 ensemble (positif)", DEFAULT_SPEED, 0, DEFAULT_SPEED, 0,
                  DEFAULT_SPEED, DEFAULT_DUR, use_encoder=True)

        # ------------------------------------------------------------------
        separator("FIN DES TESTS")
        print("  Tous les moteurs sont arrêtés.")

    except KeyboardInterrupt:
        print("\n[ARRET] Ctrl+C — arret propre.")
    except Exception as e:
        print(f"\n[ERREUR] {type(e).__name__}: {e}")
    finally:
        # Arrêt de secours + fermeture port
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
