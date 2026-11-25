# Questions possibles à l'examen oral (à préparer)

1. Suis le trajet de la photorésistance jusqu'à la luminosité de l'écran. Où est le filtre ? Pourquoi `alpha = 0,15` ?
2. Pourquoi `read_u16()` et une moyenne de 8 lectures ? Que fait `ATTN_11DB` ?
3. Comment la calibration (`LIGHT_RAW_DARK/BRIGHT`) fonctionne-t-elle si le capteur est « inversé » ?
4. Pourquoi `ticks_diff()` plutôt que `now - t` ? Que se passerait-il avec `sleep()` dans l'animation ?
5. Explique l'anti-rebond : que change `DEBOUNCE_MS` ? Différence entre `click`, `press` et `long` ?
6. Le PIR donne n'importe quoi au démarrage : comment le code gère-t-il ça ? Que veut dire « bloqué » ?
7. Comment sait-on que l'écran est absent ? Que se passe-t-il ensuite, et comment en sort-on ?
8. Calcule les gains : mise 25 sur le 17 gagnant ? mise 50 sur rouge perdante ? Pourquoi le 0 fait perdre le rouge ?
9. Pourquoi le buzzer est-il en PWM ? Que change le rapport cyclique ? Pourquoi 32768 ?
10. Pourquoi limiter l'anneau à 35 % ? Estime le courant maximal.
11. Modification possible : ajouter une mise « pair/impair », changer la durée du tour, ajouter un jeton de 5.
12. Diagnostic : l'écran reste blanc / l'anneau scintille / le jeu se met en veille tout de suite. Que vérifies-tu ?
