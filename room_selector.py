import pygame
import ezdxf
import sys

# Initialize Pygame
pygame.init()

# Window dimensions
WIDTH, HEIGHT = 1400, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("DXF Point Viewer - Source & Destination")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (240, 240, 240)
DARK_GRAY = (100, 100, 100)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 100, 255)
HOVER_COLOR = (220, 220, 220)

def load_dxf(filename):
    """Load DXF file and extract entities"""
    try:
        doc = ezdxf.readfile(filename)
        msp = doc.modelspace()
        
        entities = {'lines': [], 'points': [], 'circles': [], 'polylines': []}
        
        for entity in msp:
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                entities['lines'].append(((start.x, start.y), (end.x, end.y)))
            
            elif entity.dxftype() == 'LWPOLYLINE' or entity.dxftype() == 'POLYLINE':
                points = []
                try:
                    with entity.points() as vertices:
                        for vertex in vertices:
                            points.append((vertex[0], vertex[1]))
                    if points:
                        entities['polylines'].append(points)
                except:
                    pass
            
            elif entity.dxftype() == 'POINT':
                pos = entity.dxf.location
                entities['points'].append((pos.x, pos.y))
            
            elif entity.dxftype() == 'CIRCLE':
                center = entity.dxf.center
                radius = entity.dxf.radius
                entities['circles'].append(((center.x, center.y), radius))
        
        return entities
    except Exception as e:
        print(f"Error loading DXF: {e}")
        return None

def transform_coords(x, y, bounds, width, height, margin=80):
    """Transform DXF coordinates to screen coordinates"""
    min_x, max_x, min_y, max_y = bounds
    
    # Calculate scale to fit in window with margin
    scale_x = (width - 2 * margin - 250) / (max_x - min_x) if max_x != min_x else 1
    scale_y = (height - 2 * margin) / (max_y - min_y) if max_y != min_y else 1
    scale = min(scale_x, scale_y)
    
    # Transform coordinates (flip Y for screen coordinates)
    screen_x = margin + (x - min_x) * scale
    screen_y = height - margin - (y - min_y) * scale
    
    return int(screen_x), int(screen_y)

def get_bounds(entities):
    """Calculate bounding box of all entities"""
    all_x, all_y = [], []
    
    for line in entities['lines']:
        all_x.extend([line[0][0], line[1][0]])
        all_y.extend([line[0][1], line[1][1]])
    
    for polyline in entities['polylines']:
        for point in polyline:
            all_x.append(point[0])
            all_y.append(point[1])
    
    for point in entities['points']:
        all_x.append(point[0])
        all_y.append(point[1])
    
    if not all_x:
        return (0, 100, 0, 100)
    
    return (min(all_x), max(all_x), min(all_y), max(all_y))

def generate_points_from_bounds(bounds):
    """Generate 5 points within the DXF bounds"""
    min_x, max_x, min_y, max_y = bounds
    width = max_x - min_x
    height = max_y - min_y
    
    # ========================================
    # EDIT POINT POSITIONS HERE
    # Coordinates are relative to bounds (0.0 to 1.0)
    # 0.2 means 20% from the left/bottom
    # 0.5 means center
    # 0.8 means 80% from the left/bottom
    # ========================================
    points = [
        {"name": "d101", "x": min_x + width * 0.24, "y": min_y + height * 0.5},
        {"name": "d102", "x": min_x + width * 0.1, "y": min_y + height * 0.18},
        {"name": "d103", "x": min_x + width * 0.57, "y": min_y + height * 0.69},	
        {"name": "d104", "x": min_x + width * 0.57, "y": min_y + height * 0.14},
        {"name": "d105", "x": min_x + width * 0.93, "y": min_y + height * 0.5},
    ]
    # ========================================
    
    return points

class ModernDropdown:
    def __init__(self, x, y, width, height, items, title):
        self.rect = pygame.Rect(x, y, width, height)
        self.items = items
        self.title = title
        self.expanded = False
        self.selected_index = None
        self.hovered_index = -1
        self.font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 24)
        self.item_height = 45
        
    def draw(self, screen):
        # Draw title
        title_text = self.title_font.render(self.title, True, DARK_GRAY)
        screen.blit(title_text, (self.rect.x, self.rect.y - 25))
        
        # Draw main box with shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(screen, (200, 200, 200), shadow_rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, self.rect, border_radius=8)
        pygame.draw.rect(screen, DARK_GRAY, self.rect, 2, border_radius=8)
        
        # Draw selected item or placeholder
        if self.selected_index is not None:
            text = self.font.render(self.items[self.selected_index], True, BLACK)
        else:
            text = self.font.render("Choose...", True, DARK_GRAY)
        screen.blit(text, (self.rect.x + 15, self.rect.y + 10))
        
        # Draw arrow
        arrow = "▼" if not self.expanded else "▲"
        arrow_text = self.font.render(arrow, True, DARK_GRAY)
        screen.blit(arrow_text, (self.rect.x + self.rect.width - 35, self.rect.y + 8))
        
        # Draw dropdown items if expanded
        if self.expanded:
            for i, item in enumerate(self.items):
                item_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.item_height, 
                                       self.rect.width, self.item_height)
                
                if i == self.hovered_index:
                    color = HOVER_COLOR
                elif i == self.selected_index:
                    color = (200, 220, 255)
                else:
                    color = WHITE
                
                shadow_rect = item_rect.copy()
                shadow_rect.x += 2
                shadow_rect.y += 2
                pygame.draw.rect(screen, (200, 200, 200), shadow_rect, border_radius=6)
                pygame.draw.rect(screen, color, item_rect, border_radius=6)
                pygame.draw.rect(screen, DARK_GRAY, item_rect, 2, border_radius=6)
                
                item_text = self.font.render(item, True, BLACK)
                screen.blit(item_text, (item_rect.x + 15, item_rect.y + 10))
    
    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            self.expanded = not self.expanded
            return True
        
        if self.expanded:
            for i in range(len(self.items)):
                item_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.item_height,
                                       self.rect.width, self.item_height)
                if item_rect.collidepoint(pos):
                    self.selected_index = i
                    self.expanded = False
                    return True
        
        self.expanded = False
        return False
    
    def handle_hover(self, pos):
        if not self.expanded:
            self.hovered_index = -1
            return
        
        for i in range(len(self.items)):
            item_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.item_height,
                                   self.rect.width, self.item_height)
            if item_rect.collidepoint(pos):
                self.hovered_index = i
                return
        
        self.hovered_index = -1

def main():
    # Load DXF file
    dxf_file = "/home/yodayeet/Desktop/civil_project/D_block.dxf"
    entities = load_dxf(dxf_file)
    
    if entities is None:
        print("Failed to load DXF file")
        sys.exit(1)
    
    bounds = get_bounds(entities)
    
    # Print bounds for reference
    print("\n" + "="*50)
    print("DXF COORDINATE BOUNDS:")
    print(f"X range: {bounds[0]:.2f} to {bounds[1]:.2f}")
    print(f"Y range: {bounds[2]:.2f} to {bounds[3]:.2f}")
    print("="*50 + "\n")
    
    # Generate points within bounds
    POINT_DEFINITIONS = generate_points_from_bounds(bounds)
    
    # Create two dropdowns - destination moved further down to y=300
    point_names = [p["name"] for p in POINT_DEFINITIONS]
    source_dropdown = ModernDropdown(WIDTH - 270, 50, 240, 50, point_names, "Select Source:")
    destination_dropdown = ModernDropdown(WIDTH - 270, 350, 240, 50, point_names, "Select Destination:")
    
    font = pygame.font.Font(None, 26)
    clock = pygame.time.Clock()
    running = True
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                source_dropdown.handle_click(event.pos)
                destination_dropdown.handle_click(event.pos)
        
        source_dropdown.handle_hover(mouse_pos)
        destination_dropdown.handle_hover(mouse_pos)
        
        screen.fill(WHITE)
        
        # Draw lines
        for line in entities['lines']:
            start = transform_coords(line[0][0], line[0][1], bounds, WIDTH, HEIGHT)
            end = transform_coords(line[1][0], line[1][1], bounds, WIDTH, HEIGHT)
            pygame.draw.line(screen, BLACK, start, end, 2)
        
        # Draw polylines
        for polyline in entities['polylines']:
            if len(polyline) > 1:
                points = [transform_coords(p[0], p[1], bounds, WIDTH, HEIGHT) for p in polyline]
                pygame.draw.lines(screen, BLACK, False, points, 2)
        
        # Draw circles
        for circle in entities['circles']:
            center = transform_coords(circle[0][0], circle[0][1], bounds, WIDTH, HEIGHT)
            scale = min((WIDTH - 350) / (bounds[1] - bounds[0]), 
                       (HEIGHT - 160) / (bounds[3] - bounds[2]))
            radius = max(1, int(circle[1] * scale))
            pygame.draw.circle(screen, BLACK, center, radius, 2)
        
        # Draw points (d101-d105)
        for i, point_def in enumerate(POINT_DEFINITIONS):
            pos = transform_coords(point_def["x"], point_def["y"], bounds, WIDTH, HEIGHT)
            
            # Determine color based on source/destination selection
            if source_dropdown.selected_index == i:
                color = RED
            elif destination_dropdown.selected_index == i:
                color = GREEN
            else:
                color = BLUE
            
            # Draw point with outline
            pygame.draw.circle(screen, color, pos, 8)
            pygame.draw.circle(screen, BLACK, pos, 8, 2)
            
            # Draw label
            label = font.render(point_def["name"], True, BLACK)
            screen.blit(label, (pos[0] + 12, pos[1] - 12))
        
        # Draw dropdowns on top
        source_dropdown.draw(screen)
        destination_dropdown.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()

