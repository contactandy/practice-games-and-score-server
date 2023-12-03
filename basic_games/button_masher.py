import pygame

pygame.init()
pygame.display.set_caption("Mash buttons!")
window = pygame.display.set_mode((200, 200))

clock = pygame.time.Clock()
countdown = 5
timer_event = pygame.USEREVENT+1
pygame.time.set_timer(timer_event, 1000)

font = pygame.font.SysFont(None, 100)
text = font.render(str(countdown), True, (0, 128, 0))


keycounter = 0

run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == timer_event:
            countdown -= 1
            text = font.render(str(countdown), True, (0, 128, 0))
            if countdown == 0:
                pygame.time.set_timer(timer_event, 0)                
                text = font.render(str(keycounter), True, (0, 128, 0))
        elif event.type == pygame.KEYDOWN:
            if countdown > 0:
                keycounter += 1

    window.fill((255, 255, 255))
    text_rect = text.get_rect(center = window.get_rect().center)
    window.blit(text, text_rect)
    pygame.display.flip()

