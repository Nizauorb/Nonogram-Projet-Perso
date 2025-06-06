import time
import pygame
import sys
import json
from tkinter import Tk, filedialog
import base64
from io import BytesIO

# ==============================
# Constantes globales
# ==============================
ZOOM_STEP = 1.2
MIN_ZOOM = 0.2
MAX_ZOOM = 4.0
INITIAL_ZOOM = 0.5
CELL_SIZE_BASE_DEFAULT = 10
TOOLBAR_HEIGHT = 40
BUTTON_WIDTH = 130
BUTTON_HEIGHT = 30
BUTTON_MARGIN = 10
CROSS_SIZE = 50
ORIGINAL_WIDTH = 0
ORIGINAL_HEIGHT = 0
grid_width = 0
grid_height = 0



# Couleurs
DRAW_COLOR = (20, 20, 20, 150)
ERASE_COLOR = (0, 0, 0, 0)
GRID_COLOR = (120, 120, 120, 100)
BACKGROUND_COLOR = (230, 230, 230)
TOOLBAR_COLOR = (50, 50, 50)
BUTTON_COLOR = (100, 100, 200)
BUTTON_HOVER = (130, 130, 230)
TEXT_COLOR = (255, 255, 255)

# Rectangles des boutons
btn_load_rect = pygame.Rect(BUTTON_MARGIN, 5, BUTTON_WIDTH, BUTTON_HEIGHT)
btn_save_rect = pygame.Rect(BUTTON_MARGIN + BUTTON_WIDTH + 10, 5, BUTTON_WIDTH, BUTTON_HEIGHT)
btn_change_bg_rect = pygame.Rect(BUTTON_MARGIN + (BUTTON_WIDTH + 10) * 2, 5, BUTTON_WIDTH, BUTTON_HEIGHT)

# ==============================
# Initialisation Pygame
# ==============================
pygame.init()
screen = pygame.display.set_mode((1, 1))
pygame.display.set_caption("Initialisation...")
clock = pygame.time.Clock()

# ==============================
# Fonctions utilitaires
# ==============================
def surface_to_base64(surface):
    data = pygame.image.tostring(surface, "RGBA")
    img_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    img_surface.blit(pygame.image.fromstring(data, surface.get_size(), "RGBA"), (0, 0))
    buffer = BytesIO()
    pygame.image.save(img_surface, buffer, ".png")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def base64_to_surface(data):
    img_data = base64.b64decode(data)
    return pygame.image.load(BytesIO(img_data))

def load_image(path, alpha=True):
    try:
        image = pygame.image.load(path).convert_alpha() if alpha else pygame.image.load(path).convert()
        return image
    except FileNotFoundError as e:
        print(f"❌ Fichier introuvable : {e}")
        return None

def get_toolbar_hover(button_rect):
    return BUTTON_HOVER if button_rect.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR

# ==============================
# Chargement initial
# ==============================
background_image = load_image("assets/empty-background.png")
if not background_image:
    pygame.quit()
    sys.exit()

cross_image = load_image("assets/exit-cross.png")
if cross_image:
    cross_image = pygame.transform.smoothscale(cross_image, (CROSS_SIZE, CROSS_SIZE))

ORIGINAL_WIDTH, ORIGINAL_HEIGHT = background_image.get_size()
CELL_SIZE_BASE = 10 if max(ORIGINAL_WIDTH, ORIGINAL_HEIGHT) <= 500 else 20

drawing_surface = pygame.Surface((ORIGINAL_WIDTH, ORIGINAL_HEIGHT), pygame.SRCALPHA)
drawing_surface.fill(ERASE_COLOR)

# Réinitialiser fenêtre plein écran
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
pygame.display.set_caption("Nonogram - Revolution")

toolbar_font = pygame.font.SysFont(None, 24)
info_font = pygame.font.SysFont(None, 24)  # Pour afficher les dimensions

# ==============================
# Variables d'état
# ==============================
zoom_factor = INITIAL_ZOOM
drawing = False
erasing = False
offset_x = (SCREEN_WIDTH - ORIGINAL_WIDTH * zoom_factor) // 2
offset_y = (SCREEN_HEIGHT - ORIGINAL_HEIGHT * zoom_factor) // 2


# ==============================
# Fonctions métiers
# ==============================
def apply_zoom(mouse_x, mouse_y, zoom_before, zoom_after):
    #Calcule le nouvel offset_x et offset_y pour que le zoom soit centré sur la souris.
    
    dx = mouse_x - offset_x
    dy = mouse_y - offset_y

    new_offset_x = mouse_x - dx * zoom_after / zoom_before
    new_offset_y = mouse_y - dy * zoom_after / zoom_before

    return int(new_offset_x), int(new_offset_y)

def apply_solution(solution):
    global drawing_surface, CELL_SIZE_BASE, ORIGINAL_WIDTH, ORIGINAL_HEIGHT
    rows = len(solution)
    cols = len(solution[0]) if rows > 0 else 0
    ORIGINAL_WIDTH = cols * CELL_SIZE_BASE
    ORIGINAL_HEIGHT = rows * CELL_SIZE_BASE
    new_drawing = pygame.Surface((ORIGINAL_WIDTH, ORIGINAL_HEIGHT), pygame.SRCALPHA)
    new_drawing.fill(ERASE_COLOR)
    for row_idx, row in enumerate(solution):
        for col_idx, value in enumerate(row):
            if value == 1:
                rect = pygame.Rect(col_idx * CELL_SIZE_BASE, row_idx * CELL_SIZE_BASE,
                                   CELL_SIZE_BASE, CELL_SIZE_BASE)
                pygame.draw.rect(new_drawing, DRAW_COLOR, rect)
    drawing_surface = new_drawing

def get_solution():
    solution = []
    for y in range(0, ORIGINAL_HEIGHT, CELL_SIZE_BASE):
        row = []
        for x in range(0, ORIGINAL_WIDTH, CELL_SIZE_BASE):
            rect = pygame.Rect(x, y, CELL_SIZE_BASE, CELL_SIZE_BASE)
            try:
                subsurf = drawing_surface.subsurface(rect)
            except ValueError:
                row.append(0)
                continue
            center_color = subsurf.get_at((CELL_SIZE_BASE // 2, CELL_SIZE_BASE // 2))
            row.append(1 if center_color.a > 0 else 0)
        solution.append(row)
    return solution

def get_groups(line):
    groups = []
    count = 0
    for value in line:
        if value == 1:
            count += 1
        elif count > 0:
            groups.append(count)
            count = 0
    if count > 0:
        groups.append(count)
    return groups

def generate_clues(solution):
    rows = [get_groups(row) for row in solution]
    cols = []
    width = len(solution[0]) if solution else 0
    height = len(solution)
    for col_idx in range(width):
        column = [solution[row_idx][col_idx] for row_idx in range(height)]
        cols.append(get_groups(column))
    return rows, cols

def pretty_format_list(data, indent=4, level=0):
    """Formateur personnalisé pour les listes imbriquées."""
    if not isinstance(data, list):
        return json.dumps(data)
    
    # Si c'est une liste de valeurs simples, on la garde sur une seule ligne
    if all(not isinstance(x, list) for x in data):
        return json.dumps(data)

    # Sinon, on formate ligne par ligne
    spaces = ' ' * (level * indent)
    inner_spaces = ' ' * ((level + 1) * indent)
    lines = []
    for item in data:
        lines.append(f"{inner_spaces}{pretty_format_list(item, indent, level + 1)}")
    return '[\n' + ',\n'.join(lines) + f'\n{spaces}]'

def save_nonogram(solution, row_clues, col_clues, background_surface):
    # Récupérer les dimensions de la grille
    grid_height = len(solution)
    grid_width = len(solution[0]) if grid_height > 0 else 0

    data = {
        "version": "1.0",
        "grid_width": grid_width,
        "grid_height": grid_height,
        "solution": solution,
        "row_clues": row_clues,
        "col_clues": col_clues,
        "background_image_b64": surface_to_base64(background_surface),
        "timestamp": int(time.time())
    }

    root = Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(
        defaultextension=".nonogram",
        filetypes=[("Nonogram File", "*.nonogram")],
        title="Enregistrer le nonogram"
    )
    if not file_path:
        return

    # On construit le JSON manuellement pour garder le format lisible
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("{\n")
        items = []
        for key, value in data.items():
            formatted_value = pretty_format_list(value, level=1) if isinstance(value, list) else json.dumps(value)
            items.append(f'    "{key}": {formatted_value}')
        f.write(',\n'.join(items))
        f.write("\n}\n")
    print(f"✅ Sauvegardé sous : {file_path}")

def load_nonogram():
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        filetypes=[("Nonogram Files", "*.nonogram")],
        title="Charger un fichier .nonogram"
    )
    if not file_path:
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Charger l'image de fond
        bg_surface = base64_to_surface(data["background_image_b64"])

        # Appliquer la solution
        apply_solution(data["solution"])

        print("✅ Fichier chargé avec succès.")

        return {
            "solution": data.get("solution"),
            "row_clues": data.get("row_clues"),
            "col_clues": data.get("col_clues"),
            "background": bg_surface,
            "grid_width": data.get("grid_width"),
            "grid_height": data.get("grid_height")
        }
    except Exception as e:
        print(f"❌ Erreur lors du chargement du fichier : {e}")
        return None
    

def draw_toolbar(screen):
    pygame.draw.rect(screen, TOOLBAR_COLOR, (0, 0, SCREEN_WIDTH, TOOLBAR_HEIGHT))
    
    # Charger
    color = get_toolbar_hover(btn_load_rect)
    pygame.draw.rect(screen, color, btn_load_rect)
    text = toolbar_font.render("Charger", True, TEXT_COLOR)
    screen.blit(text, text.get_rect(center=btn_load_rect.center))

    # Sauver
    color = get_toolbar_hover(btn_save_rect)
    pygame.draw.rect(screen, color, btn_save_rect)
    text = toolbar_font.render("Sauver", True, TEXT_COLOR)
    screen.blit(text, text.get_rect(center=btn_save_rect.center))

    # Changer BG
    color = get_toolbar_hover(btn_change_bg_rect)
    pygame.draw.rect(screen, color, btn_change_bg_rect)
    text = toolbar_font.render("Changer BG", True, TEXT_COLOR)
    screen.blit(text, text.get_rect(center=btn_change_bg_rect.center))

    # Affichage des dimensions
    grid_text = info_font.render(f"Grille : {grid_width} × {grid_height}", True, TEXT_COLOR)
    screen.blit(grid_text, (SCREEN_WIDTH - 200, 10))

   

# ==============================
# Boucle principale
# ==============================
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            x_screen, y_screen = pygame.mouse.get_pos()

            # Boutons barre d'outils
            if btn_load_rect.collidepoint(x_screen, y_screen):
                loaded_data = load_nonogram()
                if loaded_data:
                    background_image = loaded_data["background"]
                    zoom_factor = 0.5  # Réinitialiser le zoom
                    img_w = int(ORIGINAL_WIDTH * zoom_factor)
                    img_h = int(ORIGINAL_HEIGHT * zoom_factor)
                    offset_x = (SCREEN_WIDTH - img_w) // 2
                    offset_y = (SCREEN_HEIGHT - img_h) // 2

                    # Récupérer les dimensions depuis le fichier
                    grid_width = loaded_data.get("grid_width", 0)
                    grid_height = loaded_data.get("grid_height", 0)

                    # Si les dimensions sont présentes → ajuster ORIGINAL_WIDTH/HEIGHT
                    if grid_width > 0 and grid_height > 0:
                        ORIGINAL_WIDTH = grid_width * CELL_SIZE_BASE
                        ORIGINAL_HEIGHT = grid_height * CELL_SIZE_BASE
                    else:
                        # Sinon, utiliser la taille de l'image de fond
                        ORIGINAL_WIDTH, ORIGINAL_HEIGHT = background_image.get_size()

                    # Redimensionner la surface de dessin
                    new_drawing = pygame.Surface((ORIGINAL_WIDTH, ORIGINAL_HEIGHT), pygame.SRCALPHA)
                    new_drawing.fill(ERASE_COLOR)
                    drawing_surface = new_drawing

                    # Si une solution est présente, l'appliquer
                    if "solution" in loaded_data:
                        apply_solution(loaded_data["solution"])
            elif btn_save_rect.collidepoint(x_screen, y_screen):
                solution = get_solution()
                row_clues, col_clues = generate_clues(solution)
                save_nonogram(solution, row_clues, col_clues, background_image)
            elif btn_change_bg_rect.collidepoint(x_screen, y_screen):
                root = Tk()
                root.withdraw()
                file_path = filedialog.askopenfilename(
                    title="Choisir arrière-plan",
                    filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif")]
                )
                if file_path:
                    try:
                        new_bg = pygame.image.load(file_path).convert_alpha()
                        background_image = new_bg
                        ORIGINAL_WIDTH, ORIGINAL_HEIGHT = background_image.get_size()
                        drawing_surface = pygame.Surface(background_image.get_size(), pygame.SRCALPHA)
                        drawing_surface.fill(ERASE_COLOR)
                        zoom_factor = INITIAL_ZOOM
                    except Exception as e:
                        print(f"❌ Échec du chargement de l'image : {e}")

            # Croix fermeture
            cross_rect = pygame.Rect(SCREEN_WIDTH - 40, 10, 30, 30)
            if cross_rect.collidepoint(x_screen, y_screen):
                running = False

            # Dessin / Effacement
            img_w = int(ORIGINAL_WIDTH * zoom_factor)
            img_h = int(ORIGINAL_HEIGHT * zoom_factor)
            rel_x = x_screen - offset_x
            rel_y = y_screen - offset_y
            x_orig, y_orig = int(rel_x / zoom_factor), int(rel_y / zoom_factor)
            col = x_orig // CELL_SIZE_BASE
            row = y_orig // CELL_SIZE_BASE
            rect = pygame.Rect(col * CELL_SIZE_BASE, row * CELL_SIZE_BASE, CELL_SIZE_BASE, CELL_SIZE_BASE)

            if event.button == 1:  # Clic gauche → dessiner
                drawing = True
                pygame.draw.rect(drawing_surface, DRAW_COLOR, rect)
            elif event.button == 3:  # Clic droit → effacer
                erasing = True
                pygame.draw.rect(drawing_surface, ERASE_COLOR, rect)
            elif event.button == 4:  # Molette haut → zoom +
                old_zoom = zoom_factor
                zoom_factor = min(zoom_factor * ZOOM_STEP, MAX_ZOOM)
                x_mouse, y_mouse = pygame.mouse.get_pos()
                offset_x, offset_y = apply_zoom(x_mouse, y_mouse, old_zoom, zoom_factor)

                # Recentre si le zoom est très petit
                if zoom_factor <= 0.5:
                    img_w = int(ORIGINAL_WIDTH * zoom_factor)
                    img_h = int(ORIGINAL_HEIGHT * zoom_factor)
                    offset_x = (SCREEN_WIDTH - img_w) // 2
                    offset_y = (SCREEN_HEIGHT - img_h) // 2

            elif event.button == 5:  # Molette bas → zoom -
                old_zoom = zoom_factor
                zoom_factor = max(zoom_factor / ZOOM_STEP, MIN_ZOOM)
                x_mouse, y_mouse = pygame.mouse.get_pos()
                offset_x, offset_y = apply_zoom(x_mouse, y_mouse, old_zoom, zoom_factor)

                # Recentre si le zoom est très petit
                if zoom_factor <= 0.5:
                    img_w = int(ORIGINAL_WIDTH * zoom_factor)
                    img_h = int(ORIGINAL_HEIGHT * zoom_factor)
                    offset_x = (SCREEN_WIDTH - img_w) // 2
                    offset_y = (SCREEN_HEIGHT - img_h) // 2

        elif event.type == pygame.MOUSEBUTTONUP:
            drawing = False
            erasing = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                drawing_surface.fill(ERASE_COLOR)
            elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                solution = get_solution()
                row_clues, col_clues = generate_clues(solution)
                save_nonogram(solution, row_clues, col_clues, background_image)
            elif event.key == pygame.K_o and pygame.key.get_mods() & pygame.KMOD_CTRL:
                data = load_nonogram()
                if data and "solution" in data:
                    background_image = data["background"]
                    zoom_factor = INITIAL_ZOOM
                    apply_solution(data["solution"])

    # Dessin continu
    if drawing or erasing:
        x_screen, y_screen = pygame.mouse.get_pos()
        img_w = int(ORIGINAL_WIDTH * zoom_factor)
        img_h = int(ORIGINAL_HEIGHT * zoom_factor)
        rel_x = x_screen - offset_x
        rel_y = y_screen - offset_y
        x_orig, y_orig = int(rel_x / zoom_factor), int(rel_y / zoom_factor)
        col = x_orig // CELL_SIZE_BASE
        row = y_orig // CELL_SIZE_BASE
        rect = pygame.Rect(col * CELL_SIZE_BASE, row * CELL_SIZE_BASE, CELL_SIZE_BASE, CELL_SIZE_BASE)
        color = DRAW_COLOR if drawing else ERASE_COLOR
        pygame.draw.rect(drawing_surface, color, rect)

    # Affichage
    img_w = int(ORIGINAL_WIDTH * zoom_factor)
    img_h = int(ORIGINAL_HEIGHT * zoom_factor)
    scaled_bg = pygame.transform.scale(background_image, (img_w, img_h))
    scaled_draw = pygame.transform.scale(drawing_surface, (img_w, img_h))
    screen.fill(BACKGROUND_COLOR)
    screen.blit(scaled_bg, (offset_x, offset_y))
    screen.blit(scaled_draw, (offset_x, offset_y))

    # Grille
    grid_surf = pygame.Surface((img_w, img_h), pygame.SRCALPHA)
    cell_zoomed = CELL_SIZE_BASE * zoom_factor
    for x in range(0, ORIGINAL_WIDTH, CELL_SIZE_BASE):
        pygame.draw.line(grid_surf, GRID_COLOR, (x * zoom_factor, 0), (x * zoom_factor, img_h), 1)
    for y in range(0, ORIGINAL_HEIGHT, CELL_SIZE_BASE):
        pygame.draw.line(grid_surf, GRID_COLOR, (0, y * zoom_factor), (img_w, y * zoom_factor), 1)
    screen.blit(grid_surf, (offset_x, offset_y))

    draw_toolbar(screen)

    # Croix fermeture
    if cross_image:
        screen.blit(cross_image, (SCREEN_WIDTH - 60, 10 + (TOOLBAR_HEIGHT - CROSS_SIZE) // 2))

    pygame.display.flip()
    clock.tick(60)

# ==============================
# Nettoyage final
# ==============================
pygame.quit()
sys.exit()