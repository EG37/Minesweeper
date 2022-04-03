from win32api import GetSystemMetrics
import pygame
import os
import sys
from random import sample, choice
import sqlite3

# Глобальные переменные с размером экрана
SIZE = WIDTH, HEIGHT = GetSystemMetrics(0), GetSystemMetrics(1)
# Инициализация пайгейма, миксера и экрана, также шрифт
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode(SIZE)
FONT = pygame.font.Font('pixel_font.otf', int(HEIGHT / 27))
# Глобальная переменная настроек и переменные для частиц
SETTINGS = {
    'difficulty': 0,
    'easy start': True,
    'timer': True,
    'general sound': True,
    'bomb sound': True,
    'victory sound': True,
    'background': True
}
GRAVITY = 0.1
particles = pygame.sprite.Group()
# Глобальные переменные для ввода текста после победы
EDITING = False
TEXT = ""
TEXT_POS = 0
EDITING_TEXT = ""
EDITING_POS = 0
TIME = 0


# Функция для загрузки изображений
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


# Функция для загрузки звука
def load_sound(name):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл со звуком '{fullname}' не найден")
        sys.exit()
    sound = pygame.mixer.Sound(fullname)
    return sound


# Функция для смены изображения на заднем плане
def set_current_background(n=None):
    if not n:
        n = choice([1, 2, 3, 4, 5, 6])
    return pygame.transform.scale(load_image('bg' + str(n) + '.png'), (WIDTH, HEIGHT))


# Функцция для смены окна
def change_current(state):
    global CURRENT, TIME
    CURRENT.stop()
    if state == 'game':
        TIME = 0
        CURRENT = Board()
    if state == 'main menu':
        CURRENT = main_menu
    if state == 'settings':
        CURRENT = settings_menu
    if state == 'help':
        CURRENT = help_menu
    if state == 'leaderboard':
        CURRENT = leaderboard_menu
    CURRENT.set_image(set_current_background())


# Функция для смены изображений в окне помощи
def change_help(action):
    if help_image.n != 1 and action == '-':
        help_image.n -= 1
    if help_image.n != 5 and action == '+':
        help_image.n += 1
    name = 'help_' + str(help_image.n) + '.png'
    help_image.set_image(pygame.transform.scale(load_image(name), (help_width, help_side)))


# Функция для изменения настроек
def change_settings(parameter):
    if parameter == 'Лёгкое начало':
        SETTINGS['easy start'] = not SETTINGS['easy start']
    elif parameter == 'Таймер':
        SETTINGS['timer'] = not SETTINGS['timer']
    elif parameter == 'Общий звук':
        SETTINGS['general sound'] = not SETTINGS['general sound']
        SETTINGS['bomb sound'] = SETTINGS['general sound']
        bomb_sound_cbox.checked = SETTINGS['general sound']
        SETTINGS['victory sound'] = SETTINGS['general sound']
        victory_sound_cbox.checked = SETTINGS['general sound']
    elif parameter == 'Звук победы':
        SETTINGS['victory sound'] = not SETTINGS['victory sound']
    elif parameter == 'Звук поражения':
        SETTINGS['bomb sound'] = not SETTINGS['bomb sound']
    elif parameter == 'Изображение':
        SETTINGS['background'] = not SETTINGS['background']


# Функция для заполнения таблицы лидеров
def fill_leaderboard(difficulty):
    global leaderboard_menu
    fullname = os.path.join('data', "Leaderboard.db")
    con = sqlite3.connect(fullname)
    cur = con.cursor()
    data = cur.execute(f'''SELECT * FROM Players 
                                   WHERE Difficulty = {difficulty}''').fetchall()
    data.sort(key=lambda x: x[3])
    if len(leaderboard_menu.widgets) != 5:
        text = leaderboard_menu.widgets[-1].text
        if text == 'Здесь пока никого нет' or data == [] or text.split()[1] != data[-1][1]:
            leaderboard_menu.widgets = [easy_btn, med_btn, hard_btn, top_lbl, leaderboard_main_menu_btn]
    if data:
        for i in range(min(8, len(data))):
            player = str(i + 1) + '. ' + data[i][1] + ' ' + str(data[i][3]) + 'сек'
            if i == 0:
                plate = 'gold.png'
            else:
                plate = 'metal.png'
            leaderboard_menu.add_widget(Label(WIDTH * 0.375, (i + 1) * gap * 19, WIDTH // 4, gap * 15, text=player,
                                              image=plate, border_width=4))
    else:
        leaderboard_menu.add_widget(Label(0, gap * 19, WIDTH, gap * 15, text='Здесь пока никого нет'))


# Функция для смены уровня сложности
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


# Класс частицы
class Particle(pygame.sprite.Sprite):
    fire = [load_image("star.png")]
    for scale in (5, 10, 20):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))

    def __init__(self, pos, dx, dy):
        super().__init__(particles)
        self.image = choice(self.fire)
        self.rect = self.image.get_rect()
        self.velocity = [dx, dy]
        self.rect.x, self.rect.y = pos
        self.gravity = GRAVITY

    def update(self):
        self.velocity[1] += self.gravity
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        if not self.rect.colliderect((0, 0, WIDTH, HEIGHT)):
            self.kill()


# Класс анимированного спрайта
class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y, freq):
        super().__init__()
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)
        self.freq = freq
        self.n = 0

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.n += 1
        if self.n % self.freq == 0:
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]


# Класс ярлыка/лейбла
class Label:
    def __init__(self, x, y, width, height, text='', image='', border_width=0, position='center'):
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.text = text
        self.border_width = border_width
        self.position = position
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
            if 'left' in self.position:
                text_x = self.rect.x + 0.04 * self.rect.width
            if 'right' in self.position:
                text_x = self.rect.x + 0.96 * self.rect.width - text.get_width()
            if 'bottom' in self.position:
                text_y = self.rect.y + self.rect.height * 0.96 - text.get_height()
            if 'top' in self.position:
                text_y = self.rect.y + self.rect.height * 0.04
            screen.blit(text, (text_x, text_y))
        if self.border_width:
            pygame.draw.rect(screen, (0, 0, 0), self.rect, width=self.border_width)

    def get_event(self, type, pos, button):
        pass

    def set_text(self, text):
        self.text = text

    def set_image(self, image):
        self.image = image


# Класс кнопки
class Button:
    def __init__(self, x, y, width, height, text='', on_click=lambda x: None, image=''):
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.state = 'up'
        self.text = text
        self.on_click = on_click
        # Переменная для смены цвета кнопки при нажатии или наведении на неё
        self.colors = {
            'up': (225, 225, 225),
            'mid': (229, 241, 251),
            'down': (204, 228, 247),
        }
        if image:
            self.image = pygame.transform.scale(load_image(image), (width, height))
        else:
            self.image = None

    # Обработка нажатия или движения мыши
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

    def set_image(self, image):
        self.image = image


# Класс поля для ввода
class InputField(Button):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.text = ''
        self.recording = False

    def get_event(self, type, pos, button):
        if type == pygame.MOUSEBUTTONUP and button == 1:
            self.get_mouse_up(pos)

    def get_mouse_up(self, pos):
        if self.rect.collidepoint(pos):
            pygame.key.start_text_input()

    def draw(self):
        pygame.draw.rect(screen, (255, 255, 255), self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, width=5, border_radius=3)
        if TEXT:
            self.text = TEXT
        text = FONT.render(self.text, True, (0, 0, 0))
        text_y = self.rect.y + self.rect.height // 2 - text.get_height() // 2
        screen.blit(text, (self.rect.x + 10, text_y))


# Класс чекбокса
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
            self.rect.width = text.get_width() + int(WIDTH / 27)
            self.rect.height = int(HEIGHT / 17)

    def draw(self):
        pygame.draw.rect(screen, self.colors[self.state][1], (self.rect.x, self.rect.y, self.rect.height,
                                                              self.rect.height), border_radius=3)
        pygame.draw.rect(screen, self.colors[self.state][0], (self.rect.x, self.rect.y, self.rect.height,
                                                              self.rect.height), width=3, border_radius=3)
        if self.checked:
            pygame.draw.line(screen, self.colors[self.state][0], (self.rect.x + 3, self.rect.y + 0.5 * self.rect.height),
                             (self.rect.x + 0.5 * self.rect.height, self.rect.y + self.rect.height - 5), width=4)
            pygame.draw.line(screen, self.colors[self.state][0], (self.rect.x + 0.5 * self.rect.height,
                                                                  self.rect.y + self.rect.height - 5),
                             (self.rect.x + 0.9 * self.rect.height, self.rect.y + 0.2 * self.rect.height), width=4)

        if self.text:
            text = FONT.render(self.text, True, (0, 0, 0))
            text_x = self.rect.x + 1.2 * self.rect.height
            text_y = self.rect.y + 0.1 * self.rect.height
            screen.blit(text, (text_x, text_y))

    def get_mouse_up(self, pos):
        if self.rect.collidepoint(pos):
            self.state = 'mid'
            self.on_click(self)
            self.checked = not self.checked


# Класс меню
class Menu:
    def __init__(self, title, *widgets, image=None, image_mode=None):
        self.widgets = list(widgets)
        self.title = title
        self.active = False
        self.image_mode = image_mode
        if image:
            self.image = pygame.transform.scale(load_image(image), (WIDTH, HEIGHT))
        else:
            self.image = None

    def run(self):
        pygame.display.set_caption(self.title)
        self.active = True
        if self.image and SETTINGS['background']:
            screen.blit(self.image, (0, 0))
            image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            if self.image_mode == 'transparent':
                pygame.draw.rect(image, (240, 240, 240, 125), image.get_rect())
            elif self.image_mode == 'opaque':
                pygame.draw.rect(image, (240, 240, 240, 255), image.get_rect())
            elif self.image_mode == 'dark':
                pygame.draw.rect(image, (50, 50, 50, 195), image.get_rect())
            screen.blit(image, (0, 0))
        else:
            screen.fill((240, 240, 240))
        for widget in self.widgets:
            widget.draw()

    # Обработка нажатия или движения для всех виджетов
    def get_event(self, type, pos, button):
        if self.active:
            for widget in self.widgets:
                widget.get_event(type, pos, button)

    def stop(self):
        self.active = False

    def add_widget(self, widget):
        self.widgets.append(widget)

    def set_image(self, image):
        self.image = image


# Класс игрового поля
class Board:
    def __init__(self, image=None):
        self.active = False
        self.image = image
        # Установка размеров поля и клеток
        if SETTINGS['difficulty'] == 0:
            self.field_size = (8, 8)
            self.flags = 10
            self.cell_side = int(min(SIZE) / 9) - 4
        else:
            self.set_cells_size()

        # Виджеты поля
        self.restart_button = Button((WIDTH - self.cell_side) // 2, gap * 1.3, self.cell_side, self.cell_side,
                                     on_click=lambda x: change_current('game'), image='smile.png')
        self.flags_label = Label((WIDTH - self.cell_side * self.field_size[1]) // 2, gap * 1.3, self.cell_side * 1.5,
                                 self.cell_side, text=str(self.flags), border_width=3)
        self.time_label = Label((WIDTH + self.cell_side * (self.field_size[1] - 3)) // 2, gap * 1.3,
                                self.cell_side * 1.5, self.cell_side, text='0', border_width=3)
        self.help_button = Button((WIDTH - self.cell_side * (self.field_size[1] - 4)) // 2, gap * 1.3, self.cell_side,
                                  self.cell_side, text='?', on_click=lambda x: change_current('help'))
        self.pause_button = Button((WIDTH + self.cell_side * (self.field_size[1] - 6)) // 2, gap * 1.3, self.cell_side,
                                   self.cell_side, text='|  |', on_click=lambda x: self.pause())
        self.main_menu_btn = Button(WIDTH // 2 - gap * 40, HEIGHT // 4 * 3, gap * 80, gap * 20,
                                    text='Выйти в главное меню', on_click=lambda x: change_current('main menu'))
        self.continue_btn = Button(WIDTH // 2 - gap * 40, HEIGHT // 4 * 3 - gap * 22, gap * 80, gap * 20,
                                   text='Продолжить', on_click=lambda x: self.pause())
        self.input_field = InputField(WIDTH // 2 - gap * 40, HEIGHT // 4 * 3 + gap * 10, gap * 80, gap * 20)
        self.help_pause_btn = Button(WIDTH // 2 - gap * 40, HEIGHT // 4 * 3 - gap * 44, gap * 80, gap * 20,
                                     text='Как играть ?', on_click=lambda x: change_current('help'))

        self.widgets = [self.restart_button, self.flags_label, self.time_label, self.help_button, self.pause_button]

        # Переменные для работы поля
        self.left = (WIDTH - self.cell_side * self.field_size[1]) // 2
        self.top = self.cell_side + gap * 4
        self.tile_img = pygame.transform.scale(load_image('tile.png'), (self.cell_side - 1, self.cell_side - 1))
        self.flag_img = pygame.transform.scale(load_image('flag1.png'), (self.cell_side - 1, self.cell_side - 1))
        self.bomb_img = pygame.transform.scale(load_image('bomb.png'), (self.cell_side - 1, self.cell_side - 1))
        self.bomb1_img = pygame.transform.scale(load_image('bomb1.png'), (self.cell_side - 1, self.cell_side - 1))
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
        self.lost, self.won = False, False
        self.paused = False

    def set_cells_size(self):
        if SETTINGS['difficulty'] == 1:
            self.field_size = (16, 16)
            self.flags = 40
        if SETTINGS['difficulty'] == 2:
            self.field_size = (16, 30)
            self.flags = 99
        self.cell_side = int(min(SIZE) / 17) - 2

    def run(self):
        global TIME
        pygame.display.set_caption('Сапёр')
        self.active = True
        screen.fill((240, 240, 240))
        if self.image and SETTINGS['background']:
            screen.blit(self.image, (0, 0))
            pygame.draw.rect(screen, (240, 240, 240), ((WIDTH - HEIGHT) // 2, 0, HEIGHT, HEIGHT))
        if SETTINGS['timer'] and self.start_time:
            if (pygame.time.get_ticks() - self.start_time) >= 1000:
                if not self.paused:
                    self.start_time = pygame.time.get_ticks()
                    TIME += 1
            self.time_label.set_text(str(TIME))
        for widget in self.widgets:
            widget.draw()
        # Отрисовка клеток
        for i in range(self.field_size[1]):
            for j in range(self.field_size[0]):
                pygame.draw.rect(screen, (132, 132, 132), [i * self.cell_side + self.left, j * self.cell_side +
                                                           self.top, self.cell_side, self.cell_side], width=3)
                if self.field[j][i] == '#':
                    screen.blit(self.tile_img, (i * self.cell_side + self.left, j * self.cell_side + self.top + 1))
                elif self.field[j][i] == 'f':
                    screen.blit(self.flag_img, (i * self.cell_side + self.left, j * self.cell_side + self.top + 1))
                elif self.field[j][i] == 'b':
                    screen.blit(self.bomb_img, (i * self.cell_side + self.left, j * self.cell_side + self.top + 1))
                elif self.field[j][i] == '@':
                    screen.blit(self.bomb1_img, (i * self.cell_side + self.left, j * self.cell_side + self.top + 1))
                elif self.field[j][i].isnumeric() and self.field[j][i] != '0':
                    color = (0, 0, 0)
                    if 1 <= int(self.field[j][i]) <= 5:
                        color = self.colors[self.field[j][i]]
                    text = FONT.render(self.field[j][i], True, color)
                    text_x = (i + 0.5) * self.cell_side + self.left - text.get_width() // 2
                    text_y = (j + 0.5) * self.cell_side + self.top - text.get_height() // 2
                    screen.blit(text, (text_x, text_y))
        # Отрисовка дополнительных сцен
        if self.lost:
            self.show_lose_scene()
        elif self.won:
            self.show_win_scene()
        elif self.paused:
            self.show_pause_scene()

    def get_event(self, type, pos, button):
        if self.active:
            if type == pygame.MOUSEBUTTONUP and not self.lost and not self.won and not self.paused:
                cell = self.get_cell(pos)
                if cell:
                    self.on_click(cell, button)
            for widget in self.widgets:
                widget.get_event(type, pos, button)
            if self.lost:
                self.main_menu_btn.get_event(type, pos, button)
            elif self.won:
                self.input_field.get_event(type, pos, button)
            elif self.paused:
                self.main_menu_btn.get_event(type, pos, button)
                self.continue_btn.get_event(type, pos, button)
                self.help_pause_btn.get_event(type, pos, button)

    def stop(self):
        self.active = False

    # Получение клетки поля при нажатии
    def get_cell(self, mouse_pos):
        x = (mouse_pos[0] - self.left) // self.cell_side
        y = (mouse_pos[1] - self.top) // self.cell_side
        if 0 <= x <= self.field_size[1] and 0 <= y <= self.field_size[0]:
            return x, y
        return None

    # Обработка нажатия на клетку поля, примерно как в предыдущем проекте
    def on_click(self, cell, button):
        x, y = cell
        if not self.bombs_set:
            self.set_bombs(cell)
            self.set_timer()
        if button == 1:
            if self.field[y][x] != 'f':
                cells = self.check_cell(x, y)
                cells = set(cells) if cells else None
                while cells:
                    cell = cells.pop()
                    row = cell // self.field_size[1]
                    col = cell % self.field_size[1]
                    if cell not in self.clean_cells:
                        self.clean_cells.append(cell)
                    result = self.check_cell(col, row)
                    if result:
                        for i in result:
                            if i not in self.clean_cells:
                                cells.add(i)
        if button == 3:
            if self.field[y][x] == '#' and self.flags:
                self.field[y][x] = 'f'
                self.flags -= 1
            elif self.field[y][x] == 'f':
                self.field[y][x] = '#'
                self.flags += 1
            self.flags_label.set_text(str(self.flags))
        if self.flags == 0:
            self.won = True
            for i in self.field:
                if any(map(lambda c: c == '#', i)):
                    self.won = False
            if self.won:
                self.win()

    def set_bombs(self, clean_cell):
        clean_cell = clean_cell[0] + clean_cell[1] * self.field_size[1]
        numbers = [i for i in range(self.field_size[0] * self.field_size[1])]
        self.bomb_cells = sample(numbers, self.flags)
        if SETTINGS['easy start']:
            while clean_cell in self.bomb_cells:
                self.bomb_cells = sample(numbers, self.flags)
        self.bombs_set = True

    # Установка таймера
    def set_timer(self):
        if SETTINGS['timer']:
            self.start_time = pygame.time.get_ticks()

    # Проверка клетки на наличие бомбы и бомбы вокруг
    def check_cell(self, col, row):
        bombs_around = 0
        cells_around = []
        modifier = self.field_size[1]
        index = row * modifier + col
        if index in self.bomb_cells:
            self.lose(col, row)
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

    # Функция проигрыша
    def lose(self, col, row):
        # Отмечаем ту самую бомбу, на которую нажал игрок
        self.field[row][col] = 'b'
        del self.bomb_cells[self.bomb_cells.index(row * self.field_size[1] + col)]
        # Расстановка неразорвавшихся бомб на поле
        for index in self.bomb_cells:
            row = index // self.field_size[1]
            col = index % self.field_size[1]
            if self.field[row][col] != 'f':
                self.field[row][col] = '@'
        if SETTINGS['bomb sound']:
            explosion = load_sound('boom.mp3')
            explosion.play()
        if SETTINGS['timer']:
            self.time_label.set_text(str((pygame.time.get_ticks() - self.start_time) // 1000))
        self.start_time = None
        self.lost = True
        # Анимация взрыва
        self.explosion = AnimatedSprite(load_image('explosion_sheet6x2.png', -1), 6, 2, WIDTH // 2 - gap * 24,
                                        HEIGHT // 2 - gap * 24, 18)
        self.explosion.rect.x = (WIDTH - self.explosion.rect.width) // 2
        self.explosion.rect.y = (HEIGHT - self.explosion.rect.height) // 2

    # Функция выигрыша
    def win(self):
        if SETTINGS['victory sound']:
            trumpet = load_sound('victory.mp3')
            trumpet.play()
        if SETTINGS['timer']:
            self.time_label.set_text(str((pygame.time.get_ticks() - self.start_time) // 1000))
        self.start_time = None
        numbers = range(-5, 6)
        # Запуск звездочек
        for _ in range(100):
            Particle((WIDTH // 2, HEIGHT // 3), choice(numbers), choice(numbers))

    # Отрисовка сцены проигрыша
    def show_lose_scene(self):
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(image, (240, 240, 240, 125), image.get_rect())
        screen.blit(image, (0, self.cell_side + gap * 1.4))
        text = FONT.render('Вы проиграли!', True, (0, 0, 0))
        text_x = WIDTH // 2 - text.get_width() // 2
        text_y = HEIGHT // 4 - text.get_height() // 2
        screen.blit(text, (text_x, text_y))
        self.explosion.update()
        group = pygame.sprite.Group()
        group.add(self.explosion)
        group.draw(screen)
        self.main_menu_btn.draw()

    # Отрисовка сцены выигрыша
    def show_win_scene(self):
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(image, (gap * 48, gap * 48, gap * 48, gap * 25), image.get_rect())
        screen.blit(image, (0, self.cell_side + gap * 1.4))
        text = FONT.render('Вы выиграли!', True, (0, 0, 0))
        text_x = WIDTH // 2 - text.get_width() // 2
        text_y = HEIGHT // 4 - text.get_height() // 2
        screen.blit(text, (text_x, text_y))
        cup = load_image('cup.png', -1)
        cup1 = Label(0, 0, cup.get_width() * (WIDTH / 1920), cup.get_height() * (HEIGHT / 1080), image='cup.png')
        cup1.rect.x = (WIDTH - cup1.rect.width) // 2
        cup1.rect.y = (HEIGHT - cup1.rect.height) // 2
        cup1.image = pygame.transform.scale(cup, (cup1.rect.width, cup1.rect.height))
        cup1.draw()
        particles.update()
        particles.draw(screen)
        self.input_field.draw()
        Label(WIDTH // 2 - gap * 40, HEIGHT // 4 * 3 - gap * 10, gap * 80, gap * 20, text='Введите ваше имя:').draw()

    # Поставить/снять тайер с паузы
    def pause(self):
        self.paused = not self.paused

    # Отрисовка сцены паузы
    def show_pause_scene(self):
        image = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(image, (240, 240, 240, 125), image.get_rect())
        clock = pygame.transform.scale(load_image('timer.png'), (400 * (WIDTH / 1920), 300 * (HEIGHT / 1080)))
        screen.blit(image, (0, 0))
        screen.blit(clock, ((WIDTH - clock.get_width()) * 0.5 - gap, (HEIGHT - clock.get_height()) * 0.4))
        text = FONT.render('Пауза', True, (0, 0, 0))
        text_x = WIDTH // 2 - text.get_width() // 2
        text_y = HEIGHT // 4 - text.get_height() // 2
        screen.blit(text, (text_x, text_y))
        self.help_pause_btn.draw()
        self.main_menu_btn.draw()
        self.continue_btn.draw()

    def set_image(self, image):
        self.image = image


# Функция для завершения ввода текста после победы
def end_editing():
    global TEXT
    pygame.key.stop_text_input()
    if SETTINGS['timer']:
        fullname = os.path.join('data', "Leaderboard.db")
        con = sqlite3.connect(fullname)
        cur = con.cursor()
        old_time = cur.execute(f'''SELECT Time from Players
                        WHERE Name = "{TEXT}" AND Difficulty = {SETTINGS['difficulty']}''').fetchone()
        if old_time:
            if old_time[0] > TIME:
                cur.execute(f"""UPDATE Players 
                                        SET Time = {TIME}
                                        WHERE Name = '{TEXT}'""").fetchall()
        else:
            cur.execute(f"""INSERT INTO Players(Name, Difficulty, Time)
                            VALUES('{TEXT}', {SETTINGS['difficulty']}, {TIME})""").fetchall()
        con.commit()
    TEXT = ''
    change_current('main menu')


# Создание и разметка главного меню
btn_w = WIDTH // 3
btn_h = HEIGHT // 12
gap = HEIGHT // 216
title_label = Label(WIDTH // 2 - btn_w * 0.6, btn_h * 0.3, 1.2 * btn_w, 3.5 * btn_h, image='title.png')
difficulty_button = Button(btn_w, (btn_h + gap) * 4, btn_w, btn_h, text='Новичок: 8 x 8',
                           on_click=lambda x: change_difficulty(difficulty_button))
start_button = Button(btn_w, (btn_h + gap) * 5, btn_w, btn_h, text='Начать', on_click=lambda x: change_current('game'))
settings_button = Button(btn_w, (btn_h + gap) * 6, btn_w, btn_h, text='Настройки',
                         on_click=lambda x: change_current('settings'))
leaderboard_button = Button(btn_w, (btn_h + gap) * 7, btn_w, btn_h, text='Таблица лидеров',
                            on_click=lambda x: change_current('leaderboard'))
exit_button = Button(btn_w, (btn_h + gap) * 8, btn_w, btn_h, text='Выйти', on_click=lambda x: sys.exit())
main_menu = Menu('Сапёр', difficulty_button, start_button, settings_button, leaderboard_button, exit_button,
                 title_label)

# Создание и разметка окна настроек
settings_lbl = Label(gap * 4, gap * 4, gap * 40, gap * 10, text='Настройки:', position='left')
easy_start_cbox = Checkbox(gap * 5, gap * 16, WIDTH, gap * 12, text='Лёгкое начало',
                           on_click=lambda x: change_settings('Лёгкое начало'))
easy_start_cbox.checked = SETTINGS['easy start']
easy_start_lbl = Label(gap * 19, gap * 31, gap * 40, gap * 10, text='Первое открытое поле гарантированно будет пустым',
                       position='left')
timer_cbox = Checkbox(gap * 5, gap * 46, WIDTH, gap * 12, text='Таймер', on_click=lambda x: change_settings('Таймер'))
timer_cbox.checked = SETTINGS['timer']
timer_lbl = Label(gap * 19, gap * 60, gap * 20, gap * 10, text='Таймер фиксирует время, затраченное на игру, '
                                                               'позволяя занести результат в таблицу лидеров',
                  position='left')
general_sound_cbox = Checkbox(gap * 5, gap * 75, WIDTH, gap * 12, text='Общий звук',
                              on_click=lambda x: change_settings('Общий звук'))
general_sound_cbox.checked = SETTINGS['general sound']
victory_sound_cbox = Checkbox(gap * 19, gap * 90, WIDTH, gap * 12, text='Звук победы',
                              on_click=lambda x: change_settings('Звук победы'))
victory_sound_cbox.checked = SETTINGS['victory sound']
bomb_sound_cbox = Checkbox(gap * 19, gap * 110, WIDTH, gap * 12, text='Звук поражения',
                           on_click=lambda x: change_settings('Звук поражния'))
image_cbox = Checkbox(gap * 5, gap * 130, WIDTH, gap * 12, text='Фоновое изображение',
                      on_click=lambda x: change_settings('Изображение'))
image_cbox.checked = SETTINGS['background']
main_menu_btn = Button(gap * 4, HEIGHT - gap * 24, gap * 60, gap * 20, text='Выйти в меню',
                       on_click=lambda x: change_current('main menu'))
bomb_sound_cbox.checked = SETTINGS['bomb sound']
settings_menu = Menu('Настройки', easy_start_cbox, settings_lbl, easy_start_lbl, timer_cbox, timer_lbl,
                     general_sound_cbox, victory_sound_cbox, bomb_sound_cbox, main_menu_btn, image_cbox,
                     image_mode='transparent')

# Создание и разметка окна "Как играть ?"
sample_image = load_image('help_1.png')
help_side = sample_image.get_height() * (HEIGHT / 1080) * 0.65
help_width = sample_image.get_width() * (WIDTH / 1920) * 0.65
help_image = Label((WIDTH - help_width) // 2, gap * 5, help_width, help_side)
help_image.set_image(pygame.transform.scale(sample_image, (help_width, help_side)))
help_image.n = 1
previous_btn = Button(WIDTH // 2 - gap * 77, HEIGHT - gap * 25, gap * 60, gap * 20, text='< Назад',
                      on_click=lambda x: change_help('-'))
next_btn = Button(WIDTH // 2 + gap * 17, HEIGHT - gap * 25, gap * 60, gap * 20, text='Далее >',
                  on_click=lambda x: change_help('+'))
game_btn = Button((WIDTH - gap * 30) // 2, HEIGHT - gap * 25, gap * 30, gap * 20, text='Назад',
                  on_click=lambda x: change_current('game'))
help_menu = Menu('Как играть', previous_btn, next_btn, game_btn, help_image, image_mode='opaque')

# Создание и разметка окна с таблицей лидеров
easy_btn = Button(gap * 5, HEIGHT - gap * 25, gap * 45, gap * 20, text='Новичок',
                  on_click=lambda x: fill_leaderboard(0))
med_btn = Button(gap * 55, HEIGHT - gap * 25, gap * 45, gap * 20, text='Любитель',
                 on_click=lambda x: fill_leaderboard(1))
hard_btn = Button(gap * 105, HEIGHT - gap * 25, gap * 55, gap * 20, text='Профессионал',
                  on_click=lambda x: fill_leaderboard(2))
leaderboard_main_menu_btn = Button(WIDTH - gap * 60, HEIGHT - gap * 25, gap * 55, gap * 20, text='Главное меню',
                                   on_click=lambda x: change_current('main menu'))
top_lbl = Label(0, gap * 3, WIDTH, 50, text='Топ игроков:')
leaderboard_menu = Menu('Таблица лидеров', easy_btn, med_btn, hard_btn, top_lbl, leaderboard_main_menu_btn,
                        image_mode='dark')

# Глобальная переменная текущей сцены
CURRENT = main_menu
CURRENT.set_image(set_current_background())

if __name__ == '__main__':
    running = True
    while running:
        # Отрисовка текущей сцены
        CURRENT.run()
        for event in pygame.event.get():
            # Выход на Escape
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN:
                # Обработка вводимого тектса
                if EDITING:
                    if len(EDITING_TEXT) == 0:
                        EDITING = False
                    continue
                if event.key == pygame.K_BACKSPACE:
                    if len(TEXT) > 0 and TEXT_POS > 0:
                        TEXT = TEXT[:TEXT_POS - 1] + TEXT[TEXT_POS:]
                        TEXT_POS -= 1
                elif event.key == pygame.K_DELETE:
                    TEXT = TEXT[:TEXT_POS] + TEXT[TEXT_POS + 1:]
                elif event.key == pygame.K_LEFT and TEXT_POS != 0:
                    TEXT_POS -= 1
                elif event.key == pygame.K_RIGHT and TEXT_POS != len(TEXT):
                    TEXT_POS += 1
                elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    EDITING = False
                    TEXT_POS = 0
                    EDITING_TEXT = ""
                    EDITING_POS = 0
                    end_editing()
            elif event.type == pygame.TEXTEDITING:
                EDITING = True
                EDITING_TEXT = event.text
                EDITING_POS = event.start
            elif event.type == pygame.TEXTINPUT:
                EDITING = False
                EDITING_TEXT = ""
                TEXT = TEXT[:TEXT_POS] + event.text + TEXT[TEXT_POS:]
                TEXT_POS += len(event.text)

            # Обработка действий мыши текущим окном
            if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                button = None
                if event.type != pygame.MOUSEMOTION:
                    button = event.button
                CURRENT.get_event(event.type, pygame.mouse.get_pos(), button)
        pygame.display.flip()
    pygame.mixer.quit()
    pygame.quit()
