class EncounterPool:
    def __init__(self, enemies):
        self.enemies = enemies
        pass
    
    def next_enemy(self):
        # Placeholder for more complex logic
        return self.enemies[0] if self.enemies else None
        