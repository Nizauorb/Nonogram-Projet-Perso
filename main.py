import pygame
import sys


# Constantes
CELL_SIZE = 40
GRID_SIZE = 5
WIDTH = CELL_SIZE * (GRID_SIZE + 6)
HEIGHT = CELL_SIZE * (GRID_SIZE + 6)
FPS = 60


# Niveaux
levels = [
    {
        "solution": [
            [1, 0, 1, 0, 1],
            [1, 1, 0, 1, 1],
            [1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1]
        ],
        "row_clues": [[1, 1, 1], [2, 2], [5], [5], [5]],
        "col_clues": [[5], [4], [1, 3], [4], [5]]
    },
    {
        "solution": [
            [0, 1, 1, 1, 0],
            [0, 1, 0, 1, 1],
            [0, 1, 1, 1, 1],
            [1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1]
        ],
        "row_clues": [[3], [1, 2], [4], [5], [5]],
        "col_clues": [[2], [5], [1, 3], [5], [4]]
    }
]


current_level = 0
fullscreen = True
game_started = False


pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)


solution = []
row_clues = []
col_clues = []
player_grid = []


drag_new_value = None  # Valeur à appliquer pendant le drag
dragged_cells = []     # Liste des cellules déjà modifiées pendant le drag


def load_level():
    global solution, row_clues, col_clues, player_grid
    level = levels[current_level]
    solution = level["solution"]
    row_clues = level["row_clues"]
    col_clues = level["col_clues"]
    player_grid = [[-1]*GRID_SIZE for _ in range(GRID_SIZE)]


def draw_text(text, pos, color=(0,0,0)):
    img = font.render(text, True, color)
    screen.blit(img, pos)


def draw_menu():
    screen.fill((220,220,220))
    title = font.render("Menu Principal", True, (0,0,0))
    screen.blit(title, (screen.get_width()//2 - title.get_width()//2, screen.get_height()//4))
    rects = {}
    w_btn, h_btn = 200, 50
    start_rect = pygame.Rect(screen.get_width()//2 - w_btn//2, screen.get_height()//2 - 100, w_btn, h_btn)
    editor_rect = pygame.Rect(screen.get_width()//2 - w_btn//2, screen.get_height()//2 - 50, w_btn, h_btn)  
    quit_rect = pygame.Rect(screen.get_width()//2 - w_btn//2, screen.get_height()//2 + 100, w_btn, h_btn)
    fullscreen_rect = pygame.Rect(screen.get_width()//2 - w_btn//2, screen.get_height()//2 + 150, w_btn, h_btn)
    pygame.draw.rect(screen, (0, 120, 200), start_rect)
    pygame.draw.rect(screen, (150, 150, 255), editor_rect)  
    pygame.draw.rect(screen, (200, 50, 50), quit_rect)
    pygame.draw.rect(screen, (50, 150, 50), fullscreen_rect)
    draw_text("Jouer", (start_rect.x + 70, start_rect.y + 15), (255,255,255))
    draw_text("Éditeur", (editor_rect.x + 70, editor_rect.y + 15), (255,255,255))
    draw_text("Quitter", (quit_rect.x + 70, quit_rect.y + 15), (255,255,255))
    draw_text("Plein écran / Fenêtré", (fullscreen_rect.x + 15, fullscreen_rect.y + 15), (255,255,255))
    rects['start'] = start_rect
    rects['editor'] = editor_rect
    rects['quit'] = quit_rect
    rects['fullscreen'] = fullscreen_rect
    return rects


def draw_cross_button():
    size = 30
    margin = 10
    x = screen.get_width() - size - margin
    y = margin
    rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(screen, (200, 50, 50), rect)
    pygame.draw.line(screen, (255, 255, 255), (x + 5, y + 5), (x + size - 5, y + size - 5), 3)
    pygame.draw.line(screen, (255, 255, 255), (x + size - 5, y + 5), (x + 5, y + size - 5), 3)
    return rect


def draw_grid():
    screen.fill((255,255,255))
    grid_width = CELL_SIZE * (GRID_SIZE + 3)
    grid_height = CELL_SIZE * (GRID_SIZE + 3)
    offset_x = (screen.get_width() - grid_width) // 2
    offset_y = (screen.get_height() - grid_height) // 2


    for i, clues in enumerate(row_clues):
        text = " ".join(str(c) for c in clues)
        draw_text(text, (offset_x + 5, offset_y + (i+2)*CELL_SIZE + 10))


    for j, clues in enumerate(col_clues):
        for k, num in enumerate(reversed(clues)):
            draw_text(str(num), (offset_x + (j+2)*CELL_SIZE + 10, offset_y + (1-k)*15 + 10))


    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            rect = pygame.Rect(offset_x + (col+2)*CELL_SIZE, offset_y + (row+2)*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (200, 200, 200), rect, 1)
            if player_grid[row][col] == 1:
                pygame.draw.rect(screen, (0,0,0), rect.inflate(-4, -4))
            elif player_grid[row][col] == 0:
                pygame.draw.line(screen, (0,0,0), rect.topleft, rect.bottomright, 2)
                pygame.draw.line(screen, (0,0,0), rect.topright, rect.bottomleft, 2)


    cross_rect = draw_cross_button()
    if check_victory():
        draw_text("Bravo ! Puzzle complété !", (offset_x + CELL_SIZE, offset_y + CELL_SIZE), (0,150,0))
    return offset_x, offset_y, cross_rect


def get_cell_from_pos(pos, offset_x, offset_y):
    x, y = pos
    col = (x - offset_x) // CELL_SIZE - 2
    row = (y - offset_y) // CELL_SIZE - 2
    if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
        return row, col
    return None, None


def check_victory():
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if solution[i][j] == 1 and player_grid[i][j] != 1:
                return False
            if solution[i][j] == 0 and player_grid[i][j] == 1:
                return False
    return True


def switch_level():
    global current_level
    current_level = (current_level + 1) % len(levels)
    load_level()


def toggle_fullscreen():
    global fullscreen, screen
    mx, my = pygame.mouse.get_pos()
    fullscreen = not fullscreen
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.mouse.set_pos(mx, my)


# Initialisation
load_level()
menu_rects = {}
dragging = False
drag_button = None


# Boucle principale
while True:
    clock.tick(FPS)
    if not game_started:
        menu_rects = draw_menu()
    else:
        offset_x, offset_y, cross_rect = draw_grid()


    pygame.display.flip()


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if not game_started:
                if menu_rects['start'].collidepoint(event.pos):
                    game_started = True
                    load_level()
                elif menu_rects['editor'].collidepoint(event.pos):  
                    print("Ouverture de l'éditeur...")
                    import subprocess
                    subprocess.Popen(["python", "editor.py"])  # Lance editor.py dans un nouveau processus
                elif menu_rects['quit'].collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
                elif menu_rects['fullscreen'].collidepoint(event.pos):
                    toggle_fullscreen()
            else:
                if cross_rect.collidepoint(event.pos):
                    game_started = False
                else:
                    row, col = get_cell_from_pos(event.pos, offset_x, offset_y)
                    if row is not None and col is not None:
                        current_val = player_grid[row][col]
                        if event.button == 1:  # Clic gauche → noir ou effacer
                            drag_new_value = -1 if current_val == 1 else 1
                        elif event.button == 3:  # Clic droit → croix ou effacer
                            drag_new_value = -1 if current_val == 0 else 0
                        else:
                            drag_new_value = None


                        if drag_new_value is not None:
                            player_grid[row][col] = drag_new_value
                            dragging = True
                            drag_button = event.button
                            dragged_cells = [(row, col)]
        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = False
            drag_button = None
            dragged_cells = []
            drag_new_value = None
        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                row, col = get_cell_from_pos(event.pos, offset_x, offset_y)
                if row is not None and col is not None and (row, col) not in dragged_cells:
                    current_val = player_grid[row][col]
                    # Applique uniquement si différent de la nouvelle valeur attendue
                    if drag_new_value == 1 and current_val != 1:
                        player_grid[row][col] = 1
                        dragged_cells.append((row, col))
                    elif drag_new_value == 0 and current_val != 0:
                        player_grid[row][col] = 0
                        dragged_cells.append((row, col))
                    elif drag_new_value == -1:
                        if current_val == 1 or current_val == 0:
                            player_grid[row][col] = -1
                            dragged_cells.append((row, col))
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            elif event.key == pygame.K_SPACE and game_started:
                switch_level()

