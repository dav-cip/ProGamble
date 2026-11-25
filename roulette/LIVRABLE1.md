# Livrable 1 – Choix de projet et plan de projet

## 1. Problème choisi et fonction du prototype
Un appareil de jeu public (type borne d'arcade) doit attirer l'attention quand quelqu'un approche, rester lisible
dans toutes les conditions de lumière, et économiser l'énergie quand il n'est pas utilisé.
Notre prototype est une **roulette à points virtuels** : il détecte la présence (PIR), adapte la luminosité de
l'écran, de l'anneau et le volume du buzzer à la lumière ambiante (photorésistance), puis se met en veille.

## 2. Diagramme fonctionnel
```
 ENTREES                    TRAITEMENT (ESP32)                      SORTIES
 Photorésistance (A0) ──►  filtre + calibration ──► % lumière ──►  Rétroéclairage écran (PWM)
   [analogique]                                         │──────►  Intensité anneau / volume buzzer
 PIR (A1)            ──►  présence / veille ──► ÉTATS ────────►  Écran TFT ILI9341 (SPI)
   [numérique]                                (machine à états)  Anneau WS2812B (16 DEL)
 4 boutons (D2-D5)   ──►  anti-rebond ──► événements ──────────►  Buzzer passif (PWM)
   [interaction locale]                                          DEL d'état (marche/arrêt)
```
États : BOOT, SLEEP, BET, SPIN, RESULT, GAMEOVER, ERROR.

## 3. Liste préliminaire des composants
Arduino Nano ESP32, écran ILI9341 3,2" (nouveau), anneau WS2812B 16 DEL (nouveau), photorésistance,
capteur PIR, buzzer passif, DEL d'état, 4 boutons, résistance 330 Ω, breadboard, fils,
**boîtier / maquette** (console de roulette, voir `MAQUETTE.md`).

## 4. Attribution préliminaire des broches
Capteurs : A0 photorésistance (ADC), A1 PIR. Sorties : D6 rétroéclairage (PWM), A3 buzzer (PWM), D7 anneau,
A2 DEL d'état. Écran SPI : D13 SCK, D11 MOSI, D12 MISO, D10 CS, D9 DC, D8 RESET. Boutons : D2, D3, D4, D5.
(Tableau détaillé dans `README.md`.)

## 5. Répartition initiale du travail
| Membre A | Membre B |
|---|---|
| Câblage du montage et alimentation | Pilote écran et interface (`ili9341.py`, `display.py`) |
| Capteurs (`sensors.py`) et calibration | Logique du jeu (`roulette.py`) et tests |
| Anneau, buzzer, DEL (`leds.py`, `sound.py`) | Boutons, machine à états (`buttons.py`, `main.py`) |
| Construction de la maquette (découpes, fixation) | Conception de la maquette (plan, étiquettes, finition) |
| Gestion d'erreurs côté matériel | README, vidéo, journal de contribution |
Les deux membres font leurs propres commits GitHub et relisent le code de l'autre.

## 6. Maquette esthétique (exigée par l'énoncé mis à jour)
Le produit final prend la forme d'une petite **console de table de roulette** : écran, anneau sous un disque diffuseur,
boutons étiquetés, fenêtres pour le PIR et la photorésistance. Plan complet dans `MAQUETTE.md`.

## 7. Dépôt GitHub
*Lien à compléter et à transmettre à la personne enseignante.*
