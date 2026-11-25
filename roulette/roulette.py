"""
roulette.py - Logique du jeu (aucun materiel ici, donc testable sur PC).

REGLES (roulette europeenne, 37 cases : 0 a 36) :
  - ROUGE / NOIR : mise x2 (la mise est rendue + 1 fois la mise)  -> "1 contre 1"
  - Un NUMERO    : mise x36 (la mise + 35 fois la mise)           -> "35 contre 1"
  - VERT         : c'est le 0, meme gain qu'un numero : x36
  - Le 0 n'est ni rouge ni noir : une mise ROUGE ou NOIR perd sur le 0.
La mise est retiree au debut du tour. Si on gagne, on recoit mise x multiplicateur.
"""
import random
import config

# Les 18 numeros rouges de la roulette europeenne
RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

CHIPS = config.CHIPS

# Liste de toutes les mises possibles, dans l'ordre du menu :
# ROUGE, NOIR, VERT puis les numeros 0 a 36.
BETS = [("red", None), ("black", None), ("green", 0)] + [("number", n) for n in range(37)]


def color_of(number):
    """Retourne 'green', 'red' ou 'black' pour un numero de 0 a 36."""
    if number == 0:
        return "green"
    if number in RED_NUMBERS:
        return "red"
    return "black"


class Game:
    def __init__(self):
        self.balance = 0
        self.chip_index = 0
        self.bet_index = 0
        self.history = []      # tirages, le plus recent en premier
        self.stake = 0         # mise du tour en cours
        self.reset()

    def reset(self):
        """Nouvelle partie : 500 points, historique vide."""
        self.balance = config.START_BALANCE
        self.chip_index = 0
        self.bet_index = 0
        self.history = []
        self.stake = 0

    # ----- choix du jeton et de la mise -----
    @property
    def chip(self):
        return CHIPS[self.chip_index]

    def change_chip(self, step):
        self.chip_index = (self.chip_index + step) % len(CHIPS)

    def change_bet(self, step):
        self.bet_index = (self.bet_index + step) % len(BETS)

    @property
    def bet(self):
        return BETS[self.bet_index]

    def bet_name(self):
        kind, number = self.bet
        if kind == "red":
            return "RED"
        if kind == "black":
            return "BLACK"
        if kind == "green":
            return "GREEN 0"
        return "NUMBER %d" % number

    def bet_color(self):
        """Couleur de la mise : 'red', 'black' ou 'green' (un numero a la couleur de sa case)."""
        kind, number = self.bet
        if kind == "number":
            return color_of(number)
        return kind

    def bet_cells(self):
        """Ensemble des cases concernees par la mise (pour les surligner)."""
        kind, number = self.bet
        if kind == "number":
            return {number}
        if kind == "green":
            return {0}
        return {n for n in range(37) if color_of(n) == kind}

    def multiplier(self):
        """Multiplicateur total (mise comprise) si la mise gagne."""
        kind, _ = self.bet
        if kind in ("red", "black"):
            return 2
        return 36

    # ----- deroulement d'un tour -----
    def can_afford(self):
        """Vrai si le joueur a assez de points pour le jeton choisi."""
        return self.balance >= self.chip

    def is_broke(self):
        """Vrai si le joueur ne peut plus payer meme le plus petit jeton."""
        return self.balance < CHIPS[0]

    def start_spin(self):
        """Retire la mise. Retourne False (sans rien retirer) si le solde est insuffisant."""
        if not self.can_afford():
            return False
        self.stake = self.chip
        self.balance -= self.stake
        return True

    def cancel_spin(self):
        """Rembourse la mise (ex: erreur pendant le tour)."""
        self.balance += self.stake
        self.stake = 0

    def draw_number(self):
        """Tirage aleatoire d'un numero de 0 a 36."""
        return random.randrange(37)

    def wins(self, number):
        kind, bet_number = self.bet
        if kind == "number" or kind == "green":
            return number == bet_number
        return color_of(number) == kind

    def finish_spin(self, number):
        """
        Calcule le resultat du tour.
        Retourne (gagne, gain_net) : gain_net est positif si gagne, negatif sinon.
        """
        stake = self.stake
        won = self.wins(number)
        payout = stake * self.multiplier() if won else 0
        self.balance += payout
        self.stake = 0
        self.history.insert(0, number)
        del self.history[config.HISTORY_SIZE:]
        return won, payout - stake
