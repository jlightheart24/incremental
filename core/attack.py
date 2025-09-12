class AttackProfile:
    def __init__(self, cooldown_s, mp_gain_on_attack=1):
        self.cooldown_s = int(cooldown_s)
        self.mp_gain_on_attack = int(mp_gain_on_attack)
        pass
    
    def __str__(self):
        return f"Attack Profile (cd = {self.cooldown_s}) mp += {self.mp_gain_on_attack}"
    
class AttackState:
    def __init__(self):
        self.time_since_attack_s = 0.0
        pass
    
    def tick(self, dt):
        self.time_since_attack_s += float(dt)
        pass
    
    def ready(self, cooldown_s):
        if self.time_since_attack_s >= cooldown_s:
            return True
        else:
            False
            
    def reset(self):
        self.time_since_attack_s = 0.0
        pass
    
    def __str__(self):
        return f"AttackState(t = {self.time_since_attack_s})"