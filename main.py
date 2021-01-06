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
            self.get_mouse_motion(pos)
        elif type == pygame.MOUSEBUTTONDOWN:
            self.get_mouse_down(pos)
        elif type == pygame.MOUSEBUTTONUP:
            self.get_mouse_up(pos)

    def get_mouse_motion(self, pos):
        if self.rect.collidepoint(pos):
            if self.state == 'up':
                self.state = 'mid'
        else:
            self.state = 'up'

    def get_mouse_down(self, pos):
        if self.rect.collidepoint(pos):
            self.state = 'down'

    def get_mouse_up(self, pos):
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


class Checkbox(Button):
    def __init__(self, x, y, width, height, text='', on_click=lambda x: None):
        super().__init__(x, y, width, height, text=text, on_click=on_click)
        self.checked = False
        self.colors = {
            'up': ((0, 0, 0), (255, 255, 255)),
            'mid': ((0, 120, 215), (255, 255, 255)),
            'down': ((0, 84, 153), (204, 228, 247))
        }
        if text:
            text = FONT.render(self.text, True, (0, 0, 0))
            self.rect.width = text.get_width() + 75
            self.rect.height = 80

    def draw(self):
        pygame.draw.rect(screen, self.colors[self.state][1], (self.rect.x, self.rect.y + 25, 50, 50),
                         border_radius=3)
        pygame.draw.rect(screen, self.colors[self.state][0], (self.rect.x, self.rect.y + 25, 50, 50),
                         width=3, border_radius=3)
        if self.checked:
            pygame.draw.line(screen, self.colors[self.state][0], (self.rect.x + 7, self.rect.y + 50),
                             (self.rect.x + 23, self.rect.y + 66), width=4)
            pygame.draw.line(screen, self.colors[self.state][0], (self.rect.x + 23, self.rect.y + 66),
                             (self.rect.x + 40, self.rect.y + 30), width=4)

        if self.text:
            text = FONT.render(self.text, True, (0, 0, 0))
            text_x = self.rect.x + 75
            text_y = self.rect.y + 25 + text.get_height() // 2
            screen.blit(text, (text_x, text_y))

    def get_mouse_up(self, pos):
        if self.rect.collidepoint(pos):
            self.state = 'mid'
            self.on_click(self)
            self.checked = not self.checked


class Menu:
    def __init__(self, title, *widgets):
        self.widgets = widgets
        self.title = title
        self.active = False

    def run(self):
        pygame.display.set_caption(self.title)
        self.active = True
        screen.fill((240, 240, 240))
        for widget in self.widgets:
            widget.draw()

    def get_event(self, type, pos):
        if self.active:
            for widget in self.widgets:
                widget.get_event(type, pos)

    def stop(self):
        self.active = False


SIZE = WIDTH, HEIGHT = GetSystemMetrics(0), GetSystemMetrics(1)
clock = pygame.time.Clock()
pygame.init()
screen = pygame.display.set_mode(SIZE)
FONT = pygame.font.Font('pixel_font.otf', 22)
test_button = Button(10, 10, 100, 100, 'test', on_click=lambda x: print('test'))
test_checkbox = Checkbox(10, 120, 100, 100, text='ТестТестТест')
main_menu = Menu('Сапёр', test_button, test_checkbox)
current = main_menu


if __name__ == '__main__':
    running = True
    clock = pygame.time.Clock()
    while running:
        current.run()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            else:
                current.get_event(event.type, pygame.mouse.get_pos())
        pygame.display.flip()
    pygame.quit()
