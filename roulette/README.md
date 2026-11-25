# ESP32 ROULETTE – POINTS GAME

Casino de poche **à points virtuels** (aucun argent réel) sur Arduino Nano ESP32, programmé en MicroPython.
Cours 420-314 – Épreuve finale « Système embarqué interactif », automne 2026.

## But du projet
Une roulette européenne interactive : l'appareil **se réveille quand une personne approche** (capteur PIR),
**adapte sa luminosité et son volume à la lumière de la pièce** (photorésistance), et se met en veille quand
personne n'est là. Le joueur mise avec 4 boutons, la roue tourne sur l'écran, l'anneau de DEL et le buzzer.

## Membres
- Prénom Nom (A) – *à compléter*
- Prénom Nom (B) – *à compléter*

Dépôt GitHub : *à compléter*

## Matériel
| Qté | Composant | Rôle |
|---|---|---|
| 1 | Arduino Nano ESP32 (ABX00083) | Carte principale |
| 1 | Écran TFT ILI9341 3,2" SPI (non tactile) | **Composant nouveau** : affichage |
| 1 | Anneau WS2812B 24 DEL | **Composant nouveau** : animation lumineuse |
| 1 | Photorésistance (module) | Capteur **analogique** : lumière ambiante |
| 1 | Capteur PIR (module) | Capteur **numérique** : présence |
| 1 | Buzzer passif | Sortie **PWM** : sons |
| 1 | DEL d'état (module) | Sortie **numérique** marche/arrêt |
| 4 | Boutons poussoirs | Interaction locale |
| 1 | Résistance 330 Ω (condensateur ~470 µF facultatif) | Protection de l'anneau |
| – | Breadboard et fils de cavalier | Montage sans soudure |
| – | Boîtier / structure (voir `MAQUETTE.md`) | Maquette esthétique |

Les deux capteurs, les deux sorties (PWM : buzzer + rétroéclairage ; numérique : DEL d'état) et les deux
composants nouveaux sont tous visibles ou vérifiables pendant la démonstration.

## Branchements (Nano ESP32)
Les noms D2, A0… sont ceux imprimés sur la carte ; le numéro GPIO correspondant est dans `config.py`.
**Vérifie chaque correspondance sur la fiche de brochage officielle de la carte.**

| Composant | Broche du module | Broche de la carte |
|---|---|---|
| Écran | SCK | D13 |
| Écran | SDI (MOSI) | D11 |
| Écran | SDO (MISO) | D12 (sert au test de présence) |
| Écran | CS | D10 |
| Écran | DC (RS) | D9 |
| Écran | RESET | D8 |
| Écran | LED (rétroéclairage) | 3V3 (toujours allumé) |
| Écran | VCC / GND | 3V3 (ou 5V selon le module) / GND |
| Bouton PREV | un côté / l'autre côté | D2 / GND |
| Bouton NEXT | un côté / l'autre côté | D3 / GND |
| Bouton SELECT | un côté / l'autre côté | D4 / GND |
| Bouton SPIN | un côté / l'autre côté | D5 / GND |
| Anneau WS2812B | DI (connecteur d'entrée femelle) | D7 (via résistance de 330 Ω) |
| Anneau WS2812B | 5V / GND (connecteur d'entrée) | VBUS (5 V USB) / GND |
| Buzzer passif | S (signal) / GND | A3 / GND |
| Photorésistance | OUT / VCC / GND | A0 / 3V3 / GND |
| PIR | OUT / VCC / GND | A1 / VBUS (5 V) / GND |
| DEL d'état | S (signal) / GND | A2 / GND |

Tous les GND sont reliés ensemble (rail GND du breadboard).

### Alimentation et précautions
- **Anneau WS2812B** (câble prégainé) : on utilise le connecteur **d'entrée** (GND, DI, 5V). Le connecteur de
  sortie (GND, DO, 5V) reste débranché et isolé. Alimentation 5 V par VBUS (USB) ; le code limite l'intensité
  à 35 % (`RING_MAX_LEVEL`), soit ~350 mA au plus. Le condensateur de 470 µF entre 5V et GND est recommandé mais
  facultatif : sans lui, brancher le fil 5V de l'anneau AVANT de brancher l'USB, et baisser `RING_MAX_LEVEL`
  à 0.2 si l'anneau scintille. La donnée sort en 3,3 V : ça fonctionne avec un fil court.
- **Rétro-éclairage de l'écran** : la broche LED est reliée à 3V3 (toujours allumé, `PIN_TFT_BL = None`). Ne la
  branche sur une GPIO (D6, en PWM) que si le module a un transistor de rétroéclairage. Le buzzer reste la
  sortie PWM du projet.
- **Écran tactile** : les broches T_CLK, T_CS, T_DIN, T_DO, T_IRQ ne sont pas utilisées.
- Schéma de câblage : `docs/esp32_roulette_wiring.drawio` (à ouvrir avec diagrams.net).
- **PIR** : alimenté en 5 V mais sa sortie est en 3,3 V : compatible. Il faut ~30 s de préchauffage après le démarrage.
- Aucun signal à 5 V ne doit jamais entrer sur une broche de la carte.

## Installation et exécution
1. Installer MicroPython sur la carte avec l'environnement utilisé en classe.
2. Envoyer sur la carte **tous ces fichiers** (à la racine) :
   `main.py, config.py, roulette.py, ili9341.py, display.py, buttons.py, sensors.py, leds.py, sound.py, errors.py`
   (`calibrate.py` est optionnel ; le dossier `tests/` reste sur le PC).
3. Redémarrer la carte : `main.py` se lance seul, sans intervention.
4. **Calibration de la lumière** : lancer `calibrate.py`, couvrir puis éclairer le capteur, noter les valeurs
   et les copier dans `LIGHT_RAW_DARK` / `LIGHT_RAW_BRIGHT` de `config.py`.

Écran à l'envers ou couleurs inversées : changer `TFT_MADCTL` dans `config.py` (voir le commentaire).

## Utilisation
- **PREV / NEXT** : changer l'option (jeton ou mise). Maintenir = défilement rapide.
- **SELECT** : alterne entre la rangée JETON (10/25/50/100) et la rangée MISE (rouge, noir, vert, numéros 0–36).
- **SPIN** : lance la roue. **Maintenir SPIN 1,5 s** : nouvelle partie (500 points).

Règles (roulette européenne, 37 cases) : mise rouge/noir → x2 ; numéro ou vert (0) → x36 ; le 0 fait perdre
rouge et noir. La mise est retirée au lancement ; une mise supérieure au solde est refusée.

## États du système
`BOOT → BET ⇄ SPIN → RESULT → BET`, avec `SLEEP` (veille après 60 s sans présence ni bouton), `GAMEOVER`
(solde < 10) et `ERROR` (mode sûr). Réactions : l'écran se tamise en veille, l'anneau et le buzzer changent
selon l'état et le résultat, la DEL d'état s'allume 3 s sur un gain.

## Gestion des erreurs
| Situation | Détection | Réaction |
|---|---|---|
| Photorésistance débranchée / court-circuit | Lecture ≤ 50 ou ≥ 65400 pendant 3 s | `!LIGHT` dans le bandeau, luminosité de secours 70 %, retour automatique quand la lecture redevient valide |
| PIR bloqué à 1 | Signal haut 10 min sans appui de bouton | `!PIR`, le PIR est ignoré (veille gérée par les boutons), se corrige quand le signal retombe |
| Écran absent ou qui plante | Lecture de l'ID ILI9341, ou exception | Mode ERREUR : anneau rouge, DEL et bips ; nouvelle tentative toutes les 5 s ou en appuyant sur SPIN |
| Erreur imprévue pendant un tour | `try/except` dans la boucle | Mise remboursée, retour en mode sûr, aucun plantage |
| Mise supérieure au solde | `can_afford()` | Message « NOT ENOUGH POINTS » et bip |
| Plus de points | `is_broke()` | « GAME OVER », maintenir SPIN pour recommencer |

## Fonctions principales
- `main.py` : classe `App`, machine à états, `step()` (un tour de boucle) et `safe_step()`.
- `roulette.py` : `Game` (mise, gains, historique), `color_of()`.
- `sensors.py` : `LightSensor` (moyenne, filtre exponentiel, calibration en %), `PresenceSensor` (préchauffage, détection de blocage).
- `buttons.py` : anti-rebond, appui long et répétition.
- `leds.py` : `Ring` (animations par modes), `StatusLed`. `sound.py` : `Buzzer` (mélodies PWM).
- `display.py` / `ili9341.py` : interface et pilote d'écran. `errors.py` : gestion des fautes.
Tout est non bloquant (`ticks_ms()` / `ticks_diff()`).

## Tests sur PC (facultatif)
`python3 tests/test_roulette.py` et `python3 tests/test_smoke.py` simulent le jeu avec un faux matériel.
Ils vérifient les gains, les états, les pannes et la reprise. Ils ne remplacent pas le test sur le montage réel.

## Limites connues
- Un fil de signal de la photorésistance **débranché** (entrée flottante) n'est pas toujours détectable ; un court-circuit l'est.
- Un PIR débranché lit 0 : il est vu comme « personne » ; les boutons réveillent quand même l'appareil.
- Le test de présence de l'écran demande le fil MISO ; sans lui, mettre `TFT_CHECK_ID = False`.
- Police 8x8 sans accents : les messages sont en anglais ASCII.

## Utilisation de l'IA
Outil : Claude (Anthropic). Usages : proposer l'architecture en fichiers, rédiger une première version du pilote
ILI9341 et de la machine à états, générer les tests sur PC, relire le code et le débogage. Nous avons relu,
testé sur le montage et compris chaque partie. *(À compléter par l'équipe avec ce que vous avez réellement modifié.)*

## Sources externes
- Séquence d'initialisation de l'ILI9341 : suite de commandes classique de la fiche technique du contrôleur
  (reprise dans de nombreuses bibliothèques, dont Adafruit_ILI9341).
- Police 8x8 : module `framebuf` de MicroPython.
