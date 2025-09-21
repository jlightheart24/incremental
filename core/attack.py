class AttackProfile:
    def __init__(self, cooldown_s, mp_gain_on_attack=1):
        self.cooldown_s = float(cooldown_s)
        self.mp_gain_on_attack = int(mp_gain_on_attack)

    def __str__(self):
        return (
            "AttackProfile("
            f"cd={self.cooldown_s}s, mp+={self.mp_gain_on_attack})"
        )


class AttackState:
    def __init__(self):
        self.time_since_attack_s = 0.0

    def tick(self, dt):
        self.time_since_attack_s += float(dt)

    def ready(self, cooldown_s):
        return self.time_since_attack_s >= float(cooldown_s)

    def reset(self):
        self.time_since_attack_s = 0.0

    def __str__(self):
        return f"AttackState(t={self.time_since_attack_s:.2f}s)"
