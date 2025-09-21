def calc_damage(atk: int, defense: int) -> int:
    """
    Basic damage rule for this prototype.

    Spec: return max(1, atk - defense)
    Notes:
    - Coerce inputs to int.
    - We will extend later (crits, resistances, etc.).
    """

    damage = max(1, atk - defense)
    return damage
