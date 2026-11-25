# Maquette – console de table de roulette

L'énoncé exige un produit **intégré dans un boîtier esthétique** : composants, fils et microcontrôleur fixés et
organisés, éléments d'interaction et d'affichage accessibles. (Cette partie compte dans « Circuit et intégration
matérielle », 15 points.)

## Concept
Une petite console posée sur une table, façon mini table de casino : dessus vert (papier ou feutre), liseré doré,
inscription « ESP32 ROULETTE ». Dimensions de départ : environ **22 cm × 14 cm × 7 cm** (à ajuster après avoir
mesuré tes pièces).

## Disposition de la face supérieure (vue de dessus)
```
 ┌──────────────────────────────────────────────┐
 │ [PIR]  (fenêtre sur le bord avant)    [LDR]  │   LDR = photorésistance, coin éloigné de l'anneau
 │                                                │
 │   ┌─────────────────┐      ◯  roue            │
 │   │  ÉCRAN 3,2"     │     (anneau 16 DEL      │
 │   │  (découpe)      │      sous un disque     │
 │   └─────────────────┘      diffuseur)         │
 │                                                │
 │  [PREV] [NEXT] [SELECT] [SPIN]      ● DEL état │
 └──────────────────────────────────────────────┘
   Côté arrière : ouverture USB-C (alimentation + programmation)
```

## Règles de conception (importantes pour que ça marche)
1. **Photorésistance** : la placer dans un coin, loin de l'anneau et de l'écran, avec un petit tube ou une
   cloison qui bloque leur lumière. Sinon l'anneau change la « lumière ambiante » mesurée et la luminosité oscille.
2. **PIR** : sa fenêtre doit regarder vers l'extérieur (côté joueur), sans cloison devant la lentille.
3. **Anneau** : placer un disque diffuseur (papier calque, plastique dépoli ou papier blanc) à 1–2 cm au-dessus
   pour que les 16 DEL forment un cercle lumineux continu. Rien de métallique près des fils de l'anneau.
4. **Écran** : découpe légèrement plus petite que la carte pour que le cadre le retienne ; fixer l'écran par l'arrière
   (colle chaude, entretoises ou languettes). Ne pas appuyer sur la vitre.
5. **Boutons** : 4 boutons en rangée, étiquetés PREV / NEXT / SELECT / SPIN, assez espacés pour les doigts.
6. **Buzzer** : à l'intérieur, face à quelques petits trous (pas de trou bouché).
7. **USB** : câble ou ouverture accessible sans ouvrir la boîte (téléversement + alimentation).
8. **Intérieur propre** : carte et breadboard fixés (ruban double face, colle chaude ou vis), fils regroupés avec des
   attaches, courts et étiquetés. Le couvercle ou un panneau doit s'ouvrir pour vérifier les raccordements.
   Demande à ton prof si la breadboard est acceptée dans la version finale.

## Matériaux possibles
Carton-mousse (foam board), contreplaqué mince, carton rigide, ou impression 3D / découpe laser si le cégep en a.
Demander au prof ce qui est disponible. Le carton-mousse est le plus rapide et donne un bon résultat peint ou recouvert.

## Plan de travail (réaliste)
| Étape | Quand |
|---|---|
| Mesurer toutes les pièces (écran, anneau, carte, boutons, capteurs) et dessiner le plan sur papier | Cette semaine |
| Faire marcher le montage sur breadboard (livrable 2) | Semaine du 30 novembre |
| Construire la boîte pendant les tests d'intégration (livrable 3) | Semaine du 7 décembre |
| Installer l'électronique, nettoyer les fils, filmer la vidéo de secours | 8–10 décembre |

Ne pas attendre la dernière semaine pour la boîte : une personne peut la construire pendant que l'autre finit le code.

## À vérifier (checklist de l'énoncé)
- [ ] Tout est fixé, rien ne bouge quand on manipule la console
- [ ] Les boutons, l'écran, l'anneau, le PIR et la photorésistance sont accessibles ou visibles pour la démo
- [ ] Les fils sont rangés, étiquetés et vérifiables
- [ ] L'allure générale est celle d'un produit fini
