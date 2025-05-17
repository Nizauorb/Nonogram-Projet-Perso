import pygame, sys

CELL_SIZE, GRID_SIZE = 40, 5
WIDTH, HEIGHT = (CELL_SIZE * (GRID_SIZE + 2)), (CELL_SIZE * (GRID_SIZE + 2))
FPS = 60

# Déf des niv
levels = [
    {
        "solution": [[1, 0, 1, 0, 1], [1, 1, 0, 1, 1], [1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [1, 1, 1, 1, 1]],
        "row_clues": [[1,1,1], [2,2], [5], [5], [5]],
        "col_clues": [[5], [4], [1,3], [4], [5]]
    }
    ,{
        "solution": [[0,1,1,1,0], [0,1,0,1,1], [0,1,1,1,0], [1,1,1,1,0], [1,1,1,1,0]],
        "row_clues": [[3], [1,2], [3], [4], [4]],
        "col_clues": [[2], [5], [1,3], [5], [1]]


    }
]

current_level = 0  # Niveau a choisir

# Récupérer le niveau actuel
def get_current_level():
    level = levels[current_level]
    return level["solution"], level["row_clues"], level["col_clues"]

# Initialisation de Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Nonogram")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

# Récupération des éléments du niveau actuel
solution, row_clues, col_clues = get_current_level()

# Grille du joueur
player_grid = [[-1] * GRID_SIZE for _ in range(GRID_SIZE)]

# Fonction pour dessiner la grille
def draw_grid():
    screen.fill((255, 255, 255))
    for i, clue in enumerate(row_clues):
        screen.blit(font.render(" ".join(map(str, clue)), True, (0, 0, 0)), (10, (i + 2) * CELL_SIZE + 10))
    for j, clue in enumerate(col_clues):
        for k, line in enumerate(clue):
            screen.blit(font.render(str(line), True, (0, 0, 0)), ((j + 2) * CELL_SIZE + 10, k * 15 + 10))
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x, y = (col + 2) * CELL_SIZE, (row + 2) * CELL_SIZE
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (200, 200, 200), rect, 1)
            if player_grid[row][col] == 1:
                pygame.draw.rect(screen, (0, 0, 0), rect.inflate(-4, -4))
            elif player_grid[row][col] == 0:
                pygame.draw.line(screen, (0, 0, 0), rect.topleft, rect.bottomright, 2)
                pygame.draw.line(screen, (0, 0, 0), rect.topright, rect.bottomleft, 2)

# Fonction pour gérer les clics
def handle_click(pos, button):
    col, row = (pos[0] // CELL_SIZE - 2), (pos[1] // CELL_SIZE - 2)
    if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
        if button == 1:
            player_grid[row][col] = -1 if player_grid[row][col] == 1 else 1
        elif button == 3:
            player_grid[row][col] = -1 if player_grid[row][col] == 0 else 0

# Fonction pour vérifier la victoire
def check_victory():
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            if player_grid[i][j] == 1 and solution[i][j] != 1:
                return False
            if player_grid[i][j] != 1 and solution[i][j] == 1:
                return False
    return True

# Fonction pour changer de niveau
def change_level():
    global current_level, solution, row_clues, col_clues, player_grid
    current_level = (current_level + 1) % len(levels)  # Passe au niveau suivant, revient au premier niveau si on est au dernier
    solution, row_clues, col_clues = get_current_level()  # Récupère les données du nouveau niveau
    player_grid = [[-1] * GRID_SIZE for _ in range(GRID_SIZE)]  # Réinitialise la grille du joueur

# Boucle principale
running = True
while running:
    clock.tick(FPS)
    draw_grid()

    if check_victory():
        screen.blit(font.render("Bravo ! Puzzle complété !", True, (0, 150, 0)), (CELL_SIZE, CELL_SIZE))
    
    pygame.display.flip()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            handle_click(event.pos, event.button)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n:  # Si la touche 'N' est pressée, changer de niveau
                change_level()

pygame.quit()
sys.exit()
