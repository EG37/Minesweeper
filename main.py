from win32api import GetSystemMetrics
import pygame


class Button:
    def __init__(self, x, y, width, height, text='', on_click=lambda x: None):
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.state = 'up'
        self.text = text
        self.on_click = on_click
        self.colors = {
            'up': (225, 225, 225),
            'mid': (229, 241, 251),
            'down': (204, 228, 247),
        }

    def get_event(self, type, pos):
        if type == pygame.MOUSEMOTION:
            if self.rect.collidepoint(pos):
                if self.state == 'up':
                    self.state = 'mid'
            else:
                self.state = 'up'
        elif type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(pos):
                self.state = 'down'
        elif type == pygame.MOUSEBUTTONUP:
            if self.rect.collidepoint(pos):
                self.state = 'mid'
                self.on_click(self)

    def draw(self):
        pygame.draw.rect(screen, self.colors[self.state], self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, width=1, border_radius=3)
        if self.text:
            text = FONT.render(self.text, True, (0, 0, 0))
            text_x = self.rect.x + self.rect.width // 2 - text.get_width() // 2
            text_y = self.rect.y + self.rect.height // 2 - text.get_height() // 2
            screen.blit(text, (text_x, text_y))


SIZE = WIDTH, HEIGHT = GetSystemMetrics(0), GetSystemMetrics(1)
clock = pygame.time.Clock()
pygame.init()
screen = pygame.display.set_mode(SIZE)
FONT = pygame.font.Font('pixel_font.otf', 22)
test_button = Button(10, 10, 100, 100, 'test', on_click=lambda x: print('test'))


if __name__ == '__main__':
    running = True
    clock = pygame.time.Clock()
    while running:
        screen.fill((240, 240, 240))
        test_button.draw()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            else:
                test_button.get_event(event.type, pygame.mouse.get_pos())
        pygame.display.flip()
    pygame.quit()
