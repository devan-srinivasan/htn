import pygame, time
if __name__ == '__main__': 
    pygame.init()
    
    white = (255, 255, 255)
    green = (0, 255, 0)
    blue = (0, 0, 128)
    
    X = 400
    Y = 400
    
    display_surface = pygame.display.set_mode((400, 400))
    pygame.display.set_caption('calibrate')
    font = pygame.font.Font('freesansbold.ttf', 20)
    nseconds = 7
    # infinite loop
    for i in range(nseconds):
    
        display_surface.fill(white)
    
        pygame.draw.circle(display_surface, (255, 0, 0), (200, 200), 5)
    
        for event in pygame.event.get():
    
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        text = font.render(f"Concentrate on the dot for {nseconds - i} seconds", True, (255, 0, 0), white)

        textRect = text.get_rect()
        textRect.center = (X // 2, Y // 2 + 70)
        display_surface.blit(text, textRect)

        pygame.display.update()
        time.sleep(1)