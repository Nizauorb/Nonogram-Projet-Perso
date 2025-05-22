import pygame
import sys
import json
from tkinter import Tk, filedialog
import base64
from io import BytesIO


def surface_to_base64(surface):
    # Convertir la surface en pixels au format PNG (RGBA)
    w, h = surface.get_size()
    size = w, h
    data = pygame.image.tostring(surface, "RGBA")  # Format RAW (RGBA)

    # Créer une surface temporaire à partir des données brutes
    img_surface = pygame.Surface(size, pygame.SRCALPHA)
    img_surface.blit(pygame.image.fromstring(data, size, "RGBA"), (0, 0))

    # Utiliser un buffer mémoire pour sauvegarder comme PNG
    buffer = BytesIO()
    pygame.image.save(img_surface, buffer, ".png")

    # Encoder en base64
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def base64_to_surface(data):
    img_data = base64.b64decode(data)
    img_file = BytesIO(img_data)
    return pygame.image.load(img_file)


# Initialisation minimale de Pygame
pygame.init()

# Créer une petite fenêtre temporaire pour activer le "video mode"
screen = pygame.display.set_mode((1, 1))
pygame.display.set_caption("Initialisation...")

# Charger l'image de fond
try:
    background_image = pygame.image.load("assets/background.png").convert_alpha()
except FileNotFoundError:
    print("❌ Fichier 'background.png' introuvable.")
    pygame.quit()
    sys.exit()

# Charger l'image de la croix pour fermer
try:
    cross_image = pygame.image.load("assets/exit-cross.png").convert_alpha()
    CROSS_SIZE = 50
    cross_image = pygame.transform.smoothscale(cross_image, (CROSS_SIZE, CROSS_SIZE))
except FileNotFoundError:
    print("⚠️ Image 'exit-cross.png' non trouvée. Utilisation d'une croix textuelle.")
    cross_image = None

# Récupérer les dimensions de l'image
ORIGINAL_WIDTH, ORIGINAL_HEIGHT = background_image.get_size()

# Réinitialiser la fenêtre en plein écran
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()
pygame.display.set_caption("Nonogram - Vue Zoomable et Centrée")

# Réglages de zoom
ZOOM_STEP = 1.2
MIN_ZOOM = 0.2
MAX_ZOOM = 4.0
zoom_factor = 0.5  # Lancement dézoomé

# Surface de dessin
drawing_surface = pygame.Surface((ORIGINAL_WIDTH, ORIGINAL_HEIGHT), pygame.SRCALPHA)

# Couleurs
DRAW_COLOR = (0, 0, 255, 150)
ERASE_COLOR = (0, 0, 0, 0)
GRID_COLOR = (200, 200, 200, 100)
BACKGROUND_COLOR = (230, 230, 230)

# Taille des blocs
CELL_SIZE_BASE = 10 if max(ORIGINAL_WIDTH, ORIGINAL_HEIGHT) <= 500 else 20

# Variables d'état
drawing = False
erasing = False

# Police
toolbar_font = pygame.font.SysFont(None, 24)

# Dimensions de la barre d'outils
TOOLBAR_HEIGHT = 40
BUTTON_WIDTH = 130
BUTTON_HEIGHT = 30
BUTTON_MARGIN = 10

# Position des boutons
btn_load_rect = pygame.Rect(BUTTON_MARGIN, 5, BUTTON_WIDTH, BUTTON_HEIGHT)
btn_save_rect = pygame.Rect(BUTTON_MARGIN + BUTTON_WIDTH + 10, 5, BUTTON_WIDTH, BUTTON_HEIGHT)
btn_change_bg_rect = pygame.Rect(BUTTON_MARGIN + (BUTTON_WIDTH + 10) * 2, 5, BUTTON_WIDTH, BUTTON_HEIGHT)

# Couleurs
TOOLBAR_COLOR = (50, 50, 50)
BUTTON_COLOR = (100, 100, 200)
BUTTON_HOVER = (130, 130, 230)
TEXT_COLOR = (255, 255, 255)

# Exit-Cross
CROSS_Y = (TOOLBAR_HEIGHT // 2) - (CROSS_SIZE // 2)

def draw_toolbar(screen):
    # Fond de la barre
    pygame.draw.rect(screen, TOOLBAR_COLOR, (0, 0, SCREEN_WIDTH, TOOLBAR_HEIGHT))

    # Bouton Charger
    btn_rect = btn_load_rect
    mouse_pos = pygame.mouse.get_pos()
    color = BUTTON_HOVER if btn_rect.collidepoint(mouse_pos) else BUTTON_COLOR
    pygame.draw.rect(screen, color, btn_rect)
    text = toolbar_font.render("Charger", True, TEXT_COLOR)
    text_rect = text.get_rect(center=btn_rect.center)
    screen.blit(text, text_rect)

    # Bouton Sauver
    btn_rect = btn_save_rect
    color = BUTTON_HOVER if btn_rect.collidepoint(mouse_pos) else BUTTON_COLOR
    pygame.draw.rect(screen, color, btn_rect)
    text = toolbar_font.render("Sauver", True, TEXT_COLOR)
    text_rect = text.get_rect(center=btn_rect.center)
    screen.blit(text, text_rect)

    # Bouton Changer BG
    btn_rect = btn_change_bg_rect
    color = BUTTON_HOVER if btn_rect.collidepoint(mouse_pos) else BUTTON_COLOR
    pygame.draw.rect(screen, color, btn_rect)
    text = toolbar_font.render("Changer BG", True, TEXT_COLOR)
    text_rect = text.get_rect(center=btn_rect.center)
    screen.blit(text, text_rect)

# Fonction pour load un fichier .nonogram
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

        # Charger l’image d’arrière-plan
        bg_surface = base64_to_surface(data["background_image_b64"])

        # Appliquer la solution
        apply_solution(data["solution"])

        print("✅ Fichier chargé avec succès.")
        return {
            "solution": data["solution"],
            "row_clues": data["row_clues"],
            "col_clues": data["col_clues"],
            "background": bg_surface
        }
    except Exception as e:
        print(f"❌ Erreur lors du chargement du fichier : {e}")
        return None
    

# Fonction pour appliquer la solution au calque    
def apply_solution(solution):
    global drawing_surface, CELL_SIZE_BASE, ORIGINAL_WIDTH, ORIGINAL_HEIGHT

    rows = len(solution)
    cols = len(solution[0]) if rows > 0 else 0

    # Ajuster la taille des blocs selon la taille de la solution
    ORIGINAL_WIDTH = cols * CELL_SIZE_BASE
    ORIGINAL_HEIGHT = rows * CELL_SIZE_BASE

    # Redimensionner la surface de dessin
    new_drawing = pygame.Surface((ORIGINAL_WIDTH, ORIGINAL_HEIGHT), pygame.SRCALPHA)
    new_drawing.fill((0, 0, 0, 0))

    for row_idx, row in enumerate(solution):
        for col_idx, value in enumerate(row):
            if value == 1:
                rect = pygame.Rect(col_idx * CELL_SIZE_BASE, row_idx * CELL_SIZE_BASE,
                                   CELL_SIZE_BASE, CELL_SIZE_BASE)
                pygame.draw.rect(new_drawing, DRAW_COLOR, rect)

    drawing_surface = new_drawing

# Fonction pour extraire la solution (matrice 1/0)
def get_solution():
    solution = []
    for y in range(0, ORIGINAL_HEIGHT, CELL_SIZE_BASE):
        row = []
        for x in range(0, ORIGINAL_WIDTH, CELL_SIZE_BASE):
            # On s'assure que le rectangle ne dépasse pas
            rect_width = min(CELL_SIZE_BASE, ORIGINAL_WIDTH - x)
            rect_height = min(CELL_SIZE_BASE, ORIGINAL_HEIGHT - y)
            rect = pygame.Rect(x, y, rect_width, rect_height)

            try:
                subsurf = drawing_surface.subsurface(rect)
            except ValueError:
                # Si malgré tout le rect est invalide (très rare), on ignore
                row.append(0)
                continue

            # On vérifie si la cellule a été coloriée
            # (on prend le pixel central pour tester)
            center_x = rect_width // 2
            center_y = rect_height // 2
            color = subsurf.get_at((center_x, center_y))

            if color.a > 0:  # Si alpha > 0 → il y a une couleur
                row.append(1)
            else:
                row.append(0)
        solution.append(row)
    return solution

# Fonction pour générer les indices
def generate_clues(solution):
    rows = [[len(group) for group in ' '.join(str(x) for x in row).split('0') if group] for row in solution]
    cols = []
    width = len(solution[0])
    height = len(solution)
    for col_idx in range(width):
        column = [solution[row_idx][col_idx] for row_idx in range(height)]
        groups = [len(g) for g in ' '.join(str(x) for x in column).split('0') if g]
        cols.append(groups)
    return rows, cols

# Fonction d'export
def save_nonogram(solution, row_clues, col_clues, background_surface):
    data = {
        "version": "1.0",
        "solution": solution,
        "row_clues": row_clues,
        "col_clues": col_clues,
        "background_image_b64": surface_to_base64(background_surface)
    }

    root = Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(
        defaultextension=".nonogram",
        filetypes=[("Nonogram File", "*.nonogram")],
        title="Enregistrer le nonogram"
    )
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, separators=(',', ':'), ensure_ascii=False)
        print(f"✅ Sauvegardé sous : {file_path}")

# --- TEST : Encodage + décodage ---
#print("🧪 Début du test encode/decode...")

# Encoder la surface en base64
#encoded = surface_to_base64(background_image)

# Décoder en surface
#decoded_surface = base64_to_surface(encoded)

# Sauvegarder temporairement comme PNG
#pygame.image.save(decoded_surface, "test_decoded.png")
#print("✅ Image décodée et sauvegardée sous 'test_decoded.png'")

# Boucle principale
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            x_screen, y_screen = pygame.mouse.get_pos()

            # Vérifier si clic sur "Charger"
            if btn_load_rect.collidepoint(x_screen, y_screen):
                loaded_data = load_nonogram()
                if loaded_data:
                    background_image = loaded_data["background"]
                    zoom_factor = 0.5
                    print("✅ Fichier chargé avec succès.")

            # Vérifier si clic sur "Sauver"
            elif btn_save_rect.collidepoint(x_screen, y_screen):
                solution = get_solution()
                row_clues, col_clues = generate_clues(solution)
                save_nonogram(solution, row_clues, col_clues, background_image)
                print("✅ Fichier sauvegardé.")

            # Vérifier si clic sur "Changer BG"
            elif btn_change_bg_rect.collidepoint(x_screen, y_screen):
                root = Tk()
                root.withdraw()
                file_path = filedialog.askopenfilename(
                    title="Sélectionner une nouvelle image d'arrière-plan",
                    filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")]
                )
                if file_path:
                    try:
                        new_bg = pygame.image.load(file_path).convert_alpha()  # Pour PNG transparents
                        background_image = new_bg
                        ORIGINAL_WIDTH, ORIGINAL_HEIGHT = background_image.get_size()

                        # Ajuster la surface de dessin à la nouvelle taille
                        new_drawing = pygame.Surface((ORIGINAL_WIDTH, ORIGINAL_HEIGHT), pygame.SRCALPHA)
                        new_drawing.fill((0, 0, 0, 0))  # Transparence totale
                        drawing_surface = new_drawing

                        zoom_factor = 0.5  # Réinitialiser le zoom
                        print("✅ Nouvelle image d’arrière-plan chargée.")
                    except Exception as e:
                        print(f"❌ Impossible de charger l'image : {e}")

            img_width_zoomed = int(ORIGINAL_WIDTH * zoom_factor)
            img_height_zoomed = int(ORIGINAL_HEIGHT * zoom_factor)
            offset_x = (SCREEN_WIDTH - img_width_zoomed) // 2
            offset_y = (SCREEN_HEIGHT - img_height_zoomed) // 2

            rel_x = x_screen - offset_x
            rel_y = y_screen - offset_y

            # Vérifier si clic sur la croix
            cross_rect = pygame.Rect(SCREEN_WIDTH - 40, 10, 30, 30)
            if cross_rect.collidepoint(x_screen, y_screen):
                running = False

            elif event.button == 1:  # Dessiner
                drawing = True
                x_orig, y_orig = int(rel_x / zoom_factor), int(rel_y / zoom_factor)
                col = x_orig // CELL_SIZE_BASE
                row = y_orig // CELL_SIZE_BASE
                rect = pygame.Rect(col * CELL_SIZE_BASE, row * CELL_SIZE_BASE, CELL_SIZE_BASE, CELL_SIZE_BASE)
                pygame.draw.rect(drawing_surface, DRAW_COLOR, rect)

            elif event.button == 3:  # Effacer
                erasing = True
                x_orig, y_orig = int(rel_x / zoom_factor), int(rel_y / zoom_factor)
                col = x_orig // CELL_SIZE_BASE
                row = y_orig // CELL_SIZE_BASE
                rect = pygame.Rect(col * CELL_SIZE_BASE, row * CELL_SIZE_BASE, CELL_SIZE_BASE, CELL_SIZE_BASE)
                pygame.draw.rect(drawing_surface, ERASE_COLOR, rect)

            elif event.button == 4:  # Molette haut → zoom +
                zoom_factor = min(zoom_factor * ZOOM_STEP, MAX_ZOOM)
            elif event.button == 5:  # Molette bas → zoom -
                zoom_factor = max(zoom_factor / ZOOM_STEP, MIN_ZOOM)          

        elif event.type == pygame.MOUSEBUTTONUP:
            drawing = False
            erasing = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                drawing_surface.fill(ERASE_COLOR)  # Effacer tout
            elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                solution = get_solution()
                row_clues, col_clues = generate_clues(solution)
                save_nonogram(solution, row_clues, col_clues, background_image)
            elif event.key == pygame.K_o and pygame.key.get_mods() & pygame.KMOD_CTRL:
                data = load_nonogram()
                if data and "solution" in data:
                    background_image = data["background"]
                    zoom_factor = 0.5  # Réinitialiser le zoom
                    print("✅ Arrière-plan mis à jour.")
                    apply_solution(data["solution"])
                    print("✅ Fichier chargé avec succès.")
                else:
                    print("⚠️ Impossible de charger ce fichier.")

    # Dessin continu en glissant
    if drawing or erasing:
        x_screen, y_screen = pygame.mouse.get_pos()

        img_width_zoomed = int(ORIGINAL_WIDTH * zoom_factor)
        img_height_zoomed = int(ORIGINAL_HEIGHT * zoom_factor)
        offset_x = (SCREEN_WIDTH - img_width_zoomed) // 2
        offset_y = (SCREEN_HEIGHT - img_height_zoomed) // 2

        rel_x = x_screen - offset_x
        rel_y = y_screen - offset_y

        x_orig, y_orig = int(rel_x / zoom_factor), int(rel_y / zoom_factor)
        col = x_orig // CELL_SIZE_BASE
        row = y_orig // CELL_SIZE_BASE
        rect = pygame.Rect(col * CELL_SIZE_BASE, row * CELL_SIZE_BASE, CELL_SIZE_BASE, CELL_SIZE_BASE)
        color = DRAW_COLOR if drawing else ERASE_COLOR
        pygame.draw.rect(drawing_surface, color, rect)

    # --- Affichage ---
    img_width_zoomed = int(ORIGINAL_WIDTH * zoom_factor)
    img_height_zoomed = int(ORIGINAL_HEIGHT * zoom_factor)
    offset_x = (SCREEN_WIDTH - img_width_zoomed) // 2
    offset_y = (SCREEN_HEIGHT - img_height_zoomed) // 2

    scaled_bg = pygame.transform.scale(background_image, (img_width_zoomed, img_height_zoomed))
    scaled_draw = pygame.transform.scale(drawing_surface, (img_width_zoomed, img_height_zoomed))

    screen.fill(BACKGROUND_COLOR)
    screen.blit(scaled_bg, (offset_x, offset_y))
    screen.blit(scaled_draw, (offset_x, offset_y))

    # Grille
    grid_surf = pygame.Surface((img_width_zoomed, img_height_zoomed), pygame.SRCALPHA)
    cell_size_zoomed = CELL_SIZE_BASE * zoom_factor
    for x in range(0, ORIGINAL_WIDTH, CELL_SIZE_BASE):
        pygame.draw.line(grid_surf, GRID_COLOR, (x * zoom_factor, 0), (x * zoom_factor, img_height_zoomed), 1)
    for y in range(0, ORIGINAL_HEIGHT, CELL_SIZE_BASE):
        pygame.draw.line(grid_surf, GRID_COLOR, (0, y * zoom_factor), (img_width_zoomed, y * zoom_factor), 1)
    screen.blit(grid_surf, (offset_x, offset_y))

    draw_toolbar(screen)

    # Croix de fermeture
    if cross_image:
        screen.blit(cross_image, (SCREEN_WIDTH - 40, CROSS_Y))
    else:
        # Fond rond pour améliorer la visibilité
        cross_center = (SCREEN_WIDTH - 25, 25)
        pygame.draw.circle(screen, (0, 0, 0, 180), cross_center, 20)  # Cercle noir semi-transparent
        # Texte blanc centré
        font = pygame.font.SysFont(None, 48)  # Police plus grosse
        cross_text = font.render("✕", True, (255, 255, 255))  # Croix blanche
        text_rect = cross_text.get_rect(center=cross_center)
        screen.blit(cross_text, text_rect)
        
    pygame.display.flip()

# Quitter proprement
pygame.quit()
sys.exit()