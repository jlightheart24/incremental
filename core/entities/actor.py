from __future__ import annotations

from core.entities.character import Character
from core.spells import Spell, get_spell
from core.stats import Mana


class Actor(Character):
    def __init__(
        self,
        name: str,
        *,
        hp: int = 10,
        atk: int = 5,
        defense: int = 1,
        speed: int = 1,
        mp_max: int = 10,
        cd: float = 0.2,
        mp_gain: int = 1,
        portrait_path: str | None = None,
        level: int = 1,
        xp: int = 0,
        spell_id: str | None = None,
    ) -> None:
        super().__init__(
            name,
            hp=hp,
            atk=atk,
            defense=defense,
            speed=speed,
            mp_max=mp_max,
            cd=cd,
            mp_gain=mp_gain,
            portrait_path=portrait_path,
        )
        self.mana = Mana(current=0, max=mp_max)
        self.level = level
        self.xp = xp
        self.xp_to_level = 100 + (level - 1) * 50
        self.magic_damage = 12
        self.current_spell: Spell | None = None
        self.spell_id: str | None = None
        if spell_id is not None:
            self.set_spell(spell_id)
        self.equipment: dict[str, object] = {}

    def gain_xp(self, amount: int) -> None:
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

    def set_spell(self, spell_id: str | None) -> None:
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

    def __str__(self) -> str:
        return f"{self.name}(HP={self.health.current}, MP={self.mana.current})"
