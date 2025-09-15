from core.stats import Stats, Health, Mana
from core.attack import AttackProfile, AttackState

class Actor:
    def __init__(self, name, *, hp=10, atk =5, defense=1, speed=1, mp_max=10, cd=0.2, mp_gain=1):
        self.name = name
        self.stats = Stats(max_hp=hp, atk=atk, defense=defense, speed=speed, mp_max=mp_max)
        self.health = Health(current=hp, max=hp)
        self.mana = Mana(current=0, max=mp_max)
        self.attack_profile = AttackProfile(cooldown_s=cd, mp_gain_on_attack=mp_gain)
        self.attack_state = AttackState()
        pass
    
    def __str__(self):
        return f"{self.name}(HP={self.health.current}, MP={self.mana.current})"
    
class Enemy:
    def __init__(self, *, hp=20, atk=3, defense=2, speed=1):
        self.stats = Stats(max_hp=hp, atk=atk, defense=defense, speed=speed)
        self.health = Health(current=hp, max=hp)
        pass
    
    def __str__(self):
        return f"Enemy(HP={self.health.current})"