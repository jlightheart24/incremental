from core.stats import Stats, Health, Mana
from core.attack import AttackProfile, AttackState
from core.spells import get_spell, Spell

class Actor:
    def __init__(
        self,
        name,
        *,
        hp=10,
        atk=5,
        defense=1,
        speed=1,
        mp_max=10,
        cd=0.2,
        mp_gain=1,
        portrait_path=None,
        level=1,
        xp=0,
        spell_id=None,
    ):
        self.name = name
        self.stats = Stats(max_hp=hp, atk=atk, defense=defense, speed=speed, mp_max=mp_max)
        self.health = Health(current=hp, max=hp)
        self.mana = Mana(current=0, max=mp_max)
        self.attack_profile = AttackProfile(cooldown_s=cd, mp_gain_on_attack=mp_gain)
        self.attack_state = AttackState()
        self.equipment = {}
        self.portrait_path = portrait_path
        self.level = level
        self.xp = xp
        self.xp_to_level = 100 + (level - 1) * 50
        self.magic_damage = 12
        self.current_spell: Spell | None = None
        self.spell_id: str | None = None
        if spell_id is not None:
            self.set_spell(spell_id)
        self.equipment = {}
        pass
    
    
    def gain_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_to_level:
            self.xp -= self.xp_to_level
            self.level += 1
            self.stats.max_hp += 5
            self.stats.atk += 2
            self.stats.defense += 1
            self.stats.speed += 1
            self.stats.mp_max += 2
            self.health.max += 5
            self.health.current = self.health.max
            self.xp_to_level = 100 + (self.level - 1) * 50
        pass
    
    def set_spell(self, spell_id):
        if spell_id is None:
            self.spell_id = None
            self.current_spell = None
            return
        spell = get_spell(spell_id)
        self.spell_id = spell_id
        self.current_spell = spell
        self.magic_damage = spell.damage
        self.stats.mp_max = spell.mp_max
        self.mana.max = spell.mp_max
        self.mana.clamp()
    
    def __str__(self):
        return f"{self.name}(HP={self.health.current}, MP={self.mana.current})"
    
class Enemy:
    def __init__(self, *, hp=20, atk=3, defense=2, speed=1, portrait_path=None, xp_reward=50):
        self.stats = Stats(max_hp=hp, atk=atk, defense=defense, speed=speed)
        self.health = Health(current=hp, max=hp)
        self.portrait_path = portrait_path
        self.xp_reward = xp_reward
        pass
    
    def __str__(self):
        return f"Enemy(HP={self.health.current})"
