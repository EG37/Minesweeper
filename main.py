from win32api import GetSystemMetrics
import pygame


SIZE = WIDTH, HEIGHT = GetSystemMetrics(0), GetSystemMetrics(1)
clock = pygame.time.Clock()
pygame.init()
screen = pygame.display.set_mode(SIZE)


if __name__ == '__main__':
    running = True
    clock = pygame.time.Clock()
    while running:
        screen.fill((240, 240, 240))
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
        pygame.display.flip()
    pygame.quit()
