from win32api import GetSystemMetrics
import pygame
import os
import sys


SETTINGS = {
    'difficulty': 0
}


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


class Label:
    def __init__(self, x, y, width, height, text='', image=''):
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.text = text
        if image:
            self.image = pygame.transform.scale(load_image(image), (width, height))
        else:
            self.image = None

    def draw(self):
        if self.image:
            screen.blit(self.image, (self.rect.x, self.rect.y))
        if self.text:
            text = FONT.render(self.text, True, (0, 0, 0))
            text_x = self.rect.x + self.rect.width // 2 - text.get_width() // 2
            text_y = self.rect.y + self.rect.height // 2 - text.get_height() // 2
            screen.blit(text, (text_x, text_y))

    def get_event(self, type, pos):
        pass


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


def change_difficulty(sender):
    levels = {
        0: 'Новичок: 8 x 8',
        1: 'Любитель: 16 х 16',
        2: 'Профессионал: 30 х 16',
    }
    SETTINGS['difficulty'] += 1
    if SETTINGS['difficulty'] >= 3:
        SETTINGS['difficulty'] = 0
    sender.text = levels[SETTINGS['difficulty']]


SIZE = WIDTH, HEIGHT = GetSystemMetrics(0), GetSystemMetrics(1)
clock = pygame.time.Clock()
pygame.init()
screen = pygame.display.set_mode(SIZE)
FONT = pygame.font.Font('pixel_font.otf', 22)
test_button = Button(10, 10, 100, 100, 'test', on_click=lambda x: print('test'))
test_checkbox = Checkbox(10, 120, 100, 100, text='ТестТестТест')
test_label = Label(0, 0, 100, 100, text='test', image='title.png')

# Создание и разметка главного меню
btn_w = WIDTH // 3
btn_h = HEIGHT // 12
title_label = Label(WIDTH // 2 - 200, btn_h, 400, 200, image='title.png')
difficulty_button = Button(btn_w, (btn_h + 5) * 4, btn_w, btn_h, text='Новичок: 8 x 8',
                           on_click=lambda x: change_difficulty(difficulty_button))
start_button = Button(btn_w, (btn_h + 5) * 5, btn_w, btn_h, text='Начать')
settings_button = Button(btn_w, (btn_h + 5) * 6, btn_w, btn_h, text='Настройки')
leaderboard_button = Button(btn_w, (btn_h + 5) * 7, btn_w, btn_h, text='Таблица лидеров')
exit_button = Button(btn_w, (btn_h + 5) * 8, btn_w, btn_h, text='Выйти', on_click=lambda x: sys.exit())
main_menu = Menu('Сапёр', difficulty_button, start_button, settings_button, leaderboard_button, exit_button,
                 title_label)

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
