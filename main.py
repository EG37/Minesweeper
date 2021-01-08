from win32api import GetSystemMetrics
import pygame
import os
import sys
from random import sample


SETTINGS = {
    'difficulty': 0,
    'easy start': True,
    'timer': True
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


def change_current(state):
    global CURRENT
    CURRENT.stop()
    if state == 'game':
        CURRENT = Board()
    if state == 'main menu':
        CURRENT = main_menu


class Label:
    def __init__(self, x, y, width, height, text='', image='', border_width=0):
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.text = text
        self.border_width = border_width
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
        if self.border_width:
            pygame.draw.rect(screen, (0, 0, 0), self.rect, width=self.border_width)

    def get_event(self, type, pos, button):
        pass

    def set_text(self, text):
        self.text = text


class Button:
    def __init__(self, x, y, width, height, text='', on_click=lambda x: None, image=''):
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.state = 'up'
        self.text = text
        self.on_click = on_click
        self.colors = {
            'up': (225, 225, 225),
            'mid': (229, 241, 251),
            'down': (204, 228, 247),
        }
        if image:
            self.image = pygame.transform.scale(load_image(image), (width, height))
        else:
            self.image = None

    def get_event(self, type, pos, button):
        if type == pygame.MOUSEMOTION:
            self.get_mouse_motion(pos)
        elif button == 1:
            if type == pygame.MOUSEBUTTONDOWN:
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
        if self.image:
            screen.blit(self.image, (self.rect.x, self.rect.y))
        if self.text:
            text = FONT.render(self.text, True, (0, 0, 0))
            text_x = self.rect.x + self.rect.width // 2 - text.get_width() // 2
            text_y = self.rect.y + self.rect.height // 2 - text.get_height() // 2
            screen.blit(text, (text_x, text_y))

    def set_text(self, text):
        self.text = text


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

    def get_event(self, type, pos, button):
        if self.active:
            for widget in self.widgets:
                widget.get_event(type, pos, button)

    def stop(self):
        self.active = False


class Board:
    def __init__(self):
        self.active = False
        if SETTINGS['difficulty'] == 0:
            self.field_size = (8, 8)
            self.flags = 10
            self.cell_side = int(min(SIZE) / 9) - 4
        else:
            self.set_cells_size()

        self.restart_button = Button((WIDTH - self.cell_side) // 2, 5, self.cell_side, self.cell_side,
                                     on_click=lambda x: change_current('game'), image='smile.png')
        self.flags_label = Label((WIDTH - self.cell_side * self.field_size[1]) // 2, 5, self.cell_side * 1.5,
                                 self.cell_side, text=str(self.flags), border_width=3)
        self.time_label = Label((WIDTH + self.cell_side * (self.field_size[1] - 3)) // 2, 5, self.cell_side * 1.5,
                                self.cell_side, text='0', border_width=3)
        self.help_button = Button((WIDTH - self.cell_side * (self.field_size[1] - 4)) // 2, 5, self.cell_side,
                                  self.cell_side, text='?', on_click=lambda x: change_current('help'))
        self.pause_button = Button((WIDTH + self.cell_side * (self.field_size[1] - 6)) // 2, 5, self.cell_side,
                                   self.cell_side, text='|  |', on_click=lambda x: change_current('pause'))

        self.widgets = [self.restart_button, self.flags_label, self.time_label, self.help_button, self.pause_button]

        self.left = (WIDTH - self.cell_side * self.field_size[1]) // 2
        self.top = self.cell_side + 20
        self.tile_img = pygame.transform.scale(load_image('tile.png'), (self.cell_side - 1, self.cell_side - 1))
        self.flag_img = pygame.transform.scale(load_image('flag1.png'), (self.cell_side - 1, self.cell_side - 1))
        self.field = [['#' for x in range(self.field_size[1])] for y in range(self.field_size[0])]
        self.bombs_set = False
        self.start_time = None
        self.clean_cells = []
        self.colors = {
            '1': (29, 12, 238),
            '2': (0, 117, 0),
            '3': (219, 0, 0),
            '4': (8, 3, 119),
            '5': (139, 0, 0)
        }

    def set_cells_size(self):
        if SETTINGS['difficulty'] == 1:
            self.field_size = (16, 16)
            self.flags = 40
        if SETTINGS['difficulty'] == 2:
            self.field_size = (16, 30)
            self.flags = 99
        self.cell_side = int(min(SIZE) / 17) - 2

    def run(self):
        pygame.display.set_caption('Сапёр')
        self.active = True
        screen.fill((240, 240, 240))
        if SETTINGS['timer'] and self.start_time:
            self.time_label.set_text(str((pygame.time.get_ticks() - self.start_time) // 1000))
        for widget in self.widgets:
            widget.draw()
        for i in range(self.field_size[1]):
            for j in range(self.field_size[0]):
                pygame.draw.rect(screen, (132, 132, 132), [i * self.cell_side + self.left, j * self.cell_side +
                                                           self.top, self.cell_side, self.cell_side], width=3)
                if self.field[j][i] == '#':
                    screen.blit(self.tile_img, (i * self.cell_side + self.left, j * self.cell_side + self.top + 1))
                elif self.field[j][i] == 'f':
                    screen.blit(self.flag_img, (i * self.cell_side + self.left, j * self.cell_side + self.top + 1))
                elif self.field[j][i].isnumeric() and self.field[j][i] != '0':
                    color = (0, 0, 0)
                    if 1 <= int(self.field[j][i]) <= 5:
                        color = self.colors[self.field[j][i]]
                    text = FONT.render(self.field[j][i], True, color)
                    text_x = (i + 0.5) * self.cell_side + self.left - text.get_width() // 2
                    text_y = (j + 0.5) * self.cell_side + self.top - text.get_height() // 2
                    screen.blit(text, (text_x, text_y))

    def get_event(self, type, pos, button):
        if self.active:
            if type == pygame.MOUSEBUTTONUP:
                cell = self.get_cell(pos)
                if cell:
                    self.on_click(cell, button)
            for widget in self.widgets:
                widget.get_event(type, pos, button)

    def stop(self):
        self.active = False

    def get_cell(self, mouse_pos):
        x = (mouse_pos[0] - self.left) // self.cell_side
        y = (mouse_pos[1] - self.top) // self.cell_side
        if 0 <= x <= self.field_size[1] and 0 <= y <= self.field_size[0]:
            return x, y
        return None

    def on_click(self, cell, button):
        x, y = cell
        if not self.bombs_set:
            self.set_bombs(cell)
            self.set_timer()
        if button == 1:
            if self.field[y][x] != 'f':
                cells = self.check_cell(x, y)
        if button == 3:
            if self.field[y][x] != 'f' and self.flags:
                self.field[y][x] = 'f'
                self.flags -= 1
            else:
                self.field[y][x] = '#'
                self.flags += 1
            self.flags_label.set_text(str(self.flags))

    def set_bombs(self, clean_cell):
        numbers = [i for i in range(self.field_size[0] * self.field_size[1])]
        self.bomb_cells = sample(numbers, self.flags)
        if SETTINGS['easy start']:
            while clean_cell in self.bomb_cells:
                self.bomb_cells = sample(numbers, self.flags)
        self.bombs_set = True

    def set_timer(self):
        if SETTINGS['timer']:
            self.start_time = pygame.time.get_ticks()

    def check_cell(self, col, row):
        bombs_around = 0
        cells_around = []
        modifier = self.field_size[1]
        index = row * modifier + col
        if index in self.bomb_cells:
            self.lose()
        else:
            if row > 0:
                if (row - 1) * modifier + col in self.bomb_cells:
                    bombs_around += 1
                cells_around.append((row - 1) * modifier + col)
                if col > 0:
                    if (row - 1) * modifier + col - 1 in self.bomb_cells:
                        bombs_around += 1
                    cells_around.append((row - 1) * modifier + col - 1)
                if col != self.field_size[1] - 1:
                    if (row - 1) * modifier + col + 1 in self.bomb_cells:
                        bombs_around += 1
                    cells_around.append((row - 1) * modifier + col + 1)
            if col > 0:
                if row * modifier + col - 1 in self.bomb_cells:
                    bombs_around += 1
                cells_around.append(row * modifier + col - 1)
            if col != self.field_size[1] - 1:
                if row * modifier + col + 1 in self.bomb_cells:
                    bombs_around += 1
                cells_around.append(row * modifier + col + 1)
            if row != self.field_size[0] - 1:
                if (row + 1) * modifier + col in self.bomb_cells:
                    bombs_around += 1
                cells_around.append((row + 1) * modifier + col)
                if col > 0:
                    if (row + 1) * modifier + col - 1 in self.bomb_cells:
                        bombs_around += 1
                    cells_around.append((row + 1) * modifier + col - 1)
                if col != self.field_size[1] - 1:
                    if (row + 1) * modifier + col + 1 in self.bomb_cells:
                        bombs_around += 1
                    cells_around.append((row + 1) * modifier + col + 1)
            # Заносим эту клетку в список чистых, он нужен,
            # чтобы аккорд не ушел в бесконечный цикл
            if index not in self.clean_cells:
                self.clean_cells.append(index)
            # Если вокруг нет бомб, возвращаем список клеток вокруг
            self.field[row][col] = str(bombs_around)
            if bombs_around == 0:
                return cells_around
            return None

    def lose(self):
        pass


def change_difficulty(sender):
    global SETTINGS
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
FONT = pygame.font.Font('pixel_font.otf', 40)
test_button = Button(10, 10, 100, 100, 'test', on_click=lambda x: print('test'))
test_checkbox = Checkbox(10, 120, 100, 100, text='ТестТестТест')
test_label = Label(0, 0, 100, 100, text='test', image='title.png')

# Создание и разметка главного меню
btn_w = WIDTH // 3
btn_h = HEIGHT // 12
title_label = Label(WIDTH // 2 - 200, btn_h, 400, 200, image='title.png')
difficulty_button = Button(btn_w, (btn_h + 5) * 4, btn_w, btn_h, text='Новичок: 8 x 8',
                           on_click=lambda x: change_difficulty(difficulty_button))
start_button = Button(btn_w, (btn_h + 5) * 5, btn_w, btn_h, text='Начать', on_click=lambda x: change_current('game'))
settings_button = Button(btn_w, (btn_h + 5) * 6, btn_w, btn_h, text='Настройки',
                         on_click=lambda x: change_current('settings'))
leaderboard_button = Button(btn_w, (btn_h + 5) * 7, btn_w, btn_h, text='Таблица лидеров',
                            on_click=lambda x: change_current('leaderboard'))
exit_button = Button(btn_w, (btn_h + 5) * 8, btn_w, btn_h, text='Выйти', on_click=lambda x: sys.exit())
main_menu = Menu('Сапёр', difficulty_button, start_button, settings_button, leaderboard_button, exit_button,
                 title_label)
CURRENT = main_menu


if __name__ == '__main__':
    running = True
    clock = pygame.time.Clock()
    while running:
        CURRENT.run()
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            button = None
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP:
                button = event.button
            CURRENT.get_event(event.type, pygame.mouse.get_pos(), button)
        clock.tick()
        pygame.display.flip()
    pygame.quit()
