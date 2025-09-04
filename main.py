import math
import item

def createItem(name, base_price, base_stat):
    new_item = item.Item(name, base_price, base_stat)
    print("Created Item")
    print(str(new_item))  # Calls new_item.__str__()
    return new_item

def main():
    money = 10
    print(f"You have {money} gold.")    
    sword = createItem("sword", 1, 1)
    for i in range(10):
        purchase = input("Do you want to purchase a sword? Y/N: ")
        if purchase.lower() == 'y':
            if money < sword.price:
                print("You don't have enough gold!")
                continue
            sword.purchase()
            money -= sword.price
            money = math.ceil(money)
            print(f"You have {money} gold left.")
        print(sword)

main()