class Stats:
    """Combat caps and base attributes.

    Keep transient values (HP/MP) in Health/Mana, not here.
    """

    def __init__(self, max_hp, atk, defense, speed, mp_max=10):
        self.max_hp = int(max_hp)
        self.atk = int(atk)
        self.defense = int(defense)
        self.speed = int(speed)
        self.mp_max = int(mp_max)

    def __str__(self):
        return (
            f"Stats(hp={self.max_hp}, atk={self.atk}, "
            f"def={self.defense}, spd={self.speed}, mp_max={self.mp_max})"
        )


class Health:
    def __init__(self, current, max):
        self.max = int(max)
        self.current = int(current)
        self.clamp()

    def clamp(self):
        if self.current < 0:
            self.current = 0
        elif self.current > self.max:
            self.current = self.max

    def is_dead(self):
        return self.current <= 0

    def ratio(self):
        return 0.0 if self.max <= 0 else self.current / self.max

    def __str__(self):
        return f"Health({self.current}/{self.max})"


class Mana:
    def __init__(self, current=0, max=10):
        self.max = int(max)
        self.current = int(current)
        self.clamp()

    def clamp(self):
        if self.current < 0:
            self.current = 0
        elif self.current > self.max:
            self.current = self.max

    def full(self):
        return self.current >= self.max

    def ratio(self):
        return 0.0 if self.max <= 0 else self.current / self.max

    def __str__(self):
        return f"Mana({self.current}/{self.max})"
