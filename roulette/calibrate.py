"""
calibrate.py - Outil de calibration du capteur de lumiere (a lancer a la main).

1. Envoie ce fichier sur l'ESP32 et lance-le (Run) depuis Thonny.
2. Pendant 20 s, il affiche la lecture brute (0-65535) chaque demi-seconde.
3. Couvre le capteur avec la main (NOIR) puis eclaire-le avec une lampe (CLAIR).
4. Note les valeurs mini / maxi affichees a la fin et copie-les dans config.py :
       LIGHT_RAW_DARK   = valeur dans le noir
       LIGHT_RAW_BRIGHT = valeur sous la lampe
(Si la valeur DIMINUE avec la lumiere, c'est normal : le programme gere les deux sens.)
"""
from machine import Pin, ADC
from time import sleep_ms
import config

adc = ADC(Pin(config.PIN_LIGHT))
adc.atten(ADC.ATTN_11DB)
low, high = 65535, 0
print("Calibration : couvre puis eclaire le capteur (20 s)...")
for _ in range(40):
    total = 0
    for _ in range(8):
        total += adc.read_u16()
    raw = total // 8
    low, high = min(low, raw), max(high, raw)
    print("brut =", raw)
    sleep_ms(500)
print("MINI =", low, " MAXI =", high)
print("Dans config.py : LIGHT_RAW_DARK / LIGHT_RAW_BRIGHT (selon le sens de ton capteur)")
