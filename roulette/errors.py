"""
errors.py - Liste des pannes (fautes) actives du systeme.

Une faute est posee quand un probleme est detecte et retiree quand il disparait,
sans redemarrer : le systeme se corrige tout seul quand c'est possible.
"""

FAULT_LIGHT = "LIGHT"     # capteur de lumiere en court-circuit ou debranche
FAULT_PIR = "PIR"         # capteur de presence bloque
FAULT_SCREEN = "SCREEN"   # ecran absent ou qui ne repond plus

_LABELS = {FAULT_LIGHT: "LIGHT", FAULT_PIR: "PIR", FAULT_SCREEN: "SCREEN"}


class FaultManager:
    def __init__(self):
        self.active = []

    def update(self, code, is_faulty):
        """Pose ou retire une faute. Retourne True si l'etat a change."""
        present = code in self.active
        if is_faulty and not present:
            self.active.append(code)
            print("FAUTE:", code)
            return True
        if not is_faulty and present:
            self.active.remove(code)
            print("FAUTE corrigee:", code)
            return True
        return False

    def has(self, code):
        return code in self.active

    def any(self):
        return len(self.active) > 0

    def label(self):
        """Texte court pour l'ecran (11 caracteres maximum), '' s'il n'y a rien."""
        if not self.active:
            return ""
        text = "!" + " !".join(_LABELS[c] for c in self.active)
        return text[:11]
