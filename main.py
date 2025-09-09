import sys
print("PYTHON USED BY VS CODE:", sys.executable)

import math
import item
import pygame

pygame.init()
WIDTH, HEIGHT = 640, 408
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Item Shop")

shop = item.Item("Shop", 1, 1)
money = 10

font_path = "assets/Orbitron-VariableFont_wght.ttf"
font_size = 32

font = pygame.font.Font(font_path, font_size)

button_rect = pygame.Rect(250, 300, 140 , 50)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if button_rect.collidepoint(event.pos):
                if money >= shop.price:
                    money -= shop.price
                    money = math.ceil(money * 100) / 100
                    shop.purchase()
                else:
                    print("Not Enough Gold!")
    
    screen.fill((30, 30, 30))
    
    # Draw item info
    item_text = font.render(f"Item: {shop.name} - Price: {shop.price} - Stat: {shop.stat}", True, (255, 255, 255))
    screen.blit(item_text, (50,50))

    # Draw player's gold
    gold_text = font.render(f"Gold: {money}", True, (255, 215, 0))
    screen.blit(gold_text, (50, 100))

    # Draw purcahse button
    pygame.draw.rect(screen, (70, 130, 180), button_rect)
    btn_text = font.render("Purchase", True, (255, 255, 255))
    screen.blit(btn_text, (button_rect.x + 20, button_rect.y +10))

    pygame.display.flip()

pygame.quit()