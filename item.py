import math

class Item:
    def __init__(self, name, base_price, base_stat, price_increase=1.2, stat_increase=1):
        self.name = name
        self.amount = 0
        self.price = base_price
        self.stat = base_stat
        self.price_increase = price_increase  # multiplier each purchase
        self.stat_increase = stat_increase    # multiplier each purchase

    def purchase(self):
        self.amount += 1
        self.price *= self.price_increase
        self.price = math.ceil(self.price * 100) / 100
        self.stat += self.stat_increase
        print(f"Purchased {self.name}!")
        print(f"You know have {self.amount}.")
        pass

    def __str__(self):
        price = math.ceil(self.price)
        return f"{self.name} (Amount {self.amount}) | Stat: {self.stat} | Next Price: {price}"