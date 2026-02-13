import pygame
import ezdxf
import sys
import os
from random import random
from typing import List, Dict, Set
import colorsys
import constants

# Initialize pygame
pygame.init()

class DXFViewer:
    def __init__(self, filename: str):
        self.filename = filename
        self.doc = None
        self.layers = []
        self.selected_layers = set()
        self.entities_by_layer = {}
        self.layer_colors = {}  # Store unique color for each layer

        # Pygame setup
        self.screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        pygame.display.set_caption(f"DXF Viewer - {os.path.basename(filename)}")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)

        # View transformation
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0
        self.dragging = False
        self.last_mouse_pos = (0, 0)

        # Checkbox parameters
        self.checkbox_size = 20
        self.checkbox_padding = 10
        self.scroll_offset = 0

        self.load_file()

    def get_layer_colours(self, n):
        BLUE = (100, 150, 255)
        GREEN = (100, 255, 100)
        RED = (255, 100, 100)
        colors = []
        for i in range(n):
            if(i%3==0):
                new_color = GREEN
            elif (i%3==1):
                new_color = BLUE
            else: 
                new_color = RED
            colors.append(new_color)

        return colors

    def load_file(self):
        """Load DXF file"""
        try:
            print("Loading DXF file...")
            self.doc = ezdxf.readfile(self.filename)
            print("✓ DXF loaded successfully")

            # Extract layers
            self.layers = [layer.dxf.name for layer in self.doc.layers]
            print(f"✓ Found {len(self.layers)} layers: {self.layers}")

            # Get colours for each layer, throw error if more than 3 layers 
            if(len(self.layers)>10):
                print("Cannot have more than 3 layers. Make sure its the right file")
                quit()
            distinct_colors = self.get_layer_colours(len(self.layers))
            self.layer_colors = {layer: color for layer, color in zip(self.layers, distinct_colors)}

            # Select all layers by default
            self.selected_layers = set(self.layers)

            # Group entities by layer
            self.group_entities_by_layer()

            # Auto-fit view
            self.auto_fit_view()

        except IOError:
            print(f"ERROR: Cannot read file '{self.filename}'")
            sys.exit(1)
        except ezdxf.DXFStructureError:
            print(f"ERROR: Invalid or corrupted DXF file.")
            sys.exit(2)
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(3)

    def group_entities_by_layer(self):
        msp = self.doc.modelspace()

        for layer in self.layers:
            self.entities_by_layer[layer] = []

        # Iterate through all entities and group by layer
        for entity in msp:
            layer_name = entity.dxf.layer
            if layer_name not in self.entities_by_layer:
                self.entities_by_layer[layer_name] = []
            self.entities_by_layer[layer_name].append(entity)

        for layer, entities in self.entities_by_layer.items():
            if len(entities) > 0:
                print(f"  Layer '{layer}': {len(entities)} entities")

    def auto_fit_view(self):
        #Calculate optimal scale and offset to fit all entities
        min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')

        msp = self.doc.modelspace()
        entity_count = 0

        for entity in msp:
            try:
                if entity.dxftype() == 'LINE':
                    min_x = min(min_x, entity.dxf.start[0], entity.dxf.end[0])
                    max_x = max(max_x, entity.dxf.start[0], entity.dxf.end[0])
                    min_y = min(min_y, entity.dxf.start[1], entity.dxf.end[1])
                    max_y = max(max_y, entity.dxf.start[1], entity.dxf.end[1])
                    entity_count += 1
                elif entity.dxftype() == 'CIRCLE':
                    cx, cy = entity.dxf.center[0], entity.dxf.center[1]
                    r = entity.dxf.radius
                    min_x, max_x = min(min_x, cx-r), max(max_x, cx+r)
                    min_y, max_y = min(min_y, cy-r), max(max_y, cy+r)
                    entity_count += 1
                elif entity.dxftype() == 'ARC':
                    cx, cy = entity.dxf.center[0], entity.dxf.center[1]
                    r = entity.dxf.radius
                    min_x, max_x = min(min_x, cx-r), max(max_x, cx+r)
                    min_y, max_y = min(min_y, cy-r), max(max_y, cy+r)
                    entity_count += 1
                elif entity.dxftype() in ['LWPOLYLINE', 'POLYLINE']:
                    for point in entity.get_points():
                        min_x = min(min_x, point[0])
                        max_x = max(max_x, point[0])
                        min_y = min(min_y, point[1])
                        max_y = max(max_y, point[1])
                    entity_count += 1
                    #to make sure that the waypoints are included in the calculation
                elif entity.dxftype() == 'INSERT': 
                    pos = entity.dxf.insert
                    min_x, max_x = min(min_x, pos[0]), max(max_x, pos[0])
                    min_y, max_y = min(min_y, pos[1]), max(max_y, pos[1])
                    entity_count += 1
            except:
                pass

        print(f"✓ Processed {entity_count} entities for display")

        if min_x != float('inf'):
            drawing_width = max_x - min_x
            drawing_height = max_y - min_y

            if drawing_width > 0 and drawing_height > 0:
                scale_x = constants.DRAWING_AREA_WIDTH * 0.8 / drawing_width
                scale_y = constants.SCREEN_HEIGHT * 0.8 / drawing_height
                self.scale = min(scale_x, scale_y)

                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2
                self.offset_x = constants.DRAWING_AREA_WIDTH / 2 - center_x * self.scale
                self.offset_y = constants.SCREEN_HEIGHT / 2 + center_y * self.scale

                print(f"✓ View auto-fitted (scale: {self.scale:.2f})")

    def world_to_screen(self, x, y):
        #Convert world coordinates to screen coordinates
        screen_x = x * self.scale + self.offset_x
        screen_y = -y * self.scale + self.offset_y
        return int(screen_x), int(screen_y)

    def get_entity_color(self, entity):
        """Get color for entity based on its layer"""
        layer_name = entity.dxf.layer
        return self.layer_colors.get(layer_name, constants.WHITE)

    def draw_entity(self, entity):
        """Draw a single entity"""
        if entity.dxf.layer not in self.selected_layers:
            return

        color = self.get_entity_color(entity)

        try:
            if entity.dxftype() == 'LINE':
                start = self.world_to_screen(entity.dxf.start[0], entity.dxf.start[1])
                end = self.world_to_screen(entity.dxf.end[0], entity.dxf.end[1])
                pygame.draw.line(self.screen, color, start, end, 2)  # Thicker lines

            elif entity.dxftype() == 'CIRCLE':
                center = self.world_to_screen(entity.dxf.center[0], entity.dxf.center[1])
                radius = int(entity.dxf.radius * self.scale)
                if radius > 0:
                    pygame.draw.circle(self.screen, color, center, radius, 2)

            elif entity.dxftype() == 'ARC':
                center = self.world_to_screen(entity.dxf.center[0], entity.dxf.center[1])
                radius = int(entity.dxf.radius * self.scale)
                if radius > 0:
                    pygame.draw.circle(self.screen, color, center, radius, 2)

            elif entity.dxftype() == 'LWPOLYLINE' or entity.dxftype() == 'POLYLINE':
                points = [self.world_to_screen(p[0], p[1]) for p in entity.get_points()]
                if len(points) > 1:
                    pygame.draw.lines(self.screen, color, entity.is_closed, points, 2)

            elif entity.dxftype() == 'SPLINE':
                try:
                    points = [self.world_to_screen(p[0], p[1]) for p in entity.flattening(0.1)]
                    if len(points) > 1:
                        pygame.draw.lines(self.screen, color, False, points, 2)
                except:
                    pass

            elif entity.dxftype() == 'INSERT':
                # Convert CAD coordinates to screen pixels
                pos = self.world_to_screen(entity.dxf.insert[0], entity.dxf.insert[1])
                
                # Draw a visual marker (a filled circle) for the waypoint
                pygame.draw.circle(self.screen, color, pos, 6) # slightly larger than lines
                
                # Extract and display the attribute text (e.g., "Node_A")
                for attrib in entity.attribs:
                    if attrib.dxf.tag in ['ID', 'NAME']:
                        text_surface = self.small_font.render(attrib.dxf.text, True, constants.WHITE)
                        self.screen.blit(text_surface, (pos[0] + 10, pos[1] - 10))
        except Exception as e:
            pass
    
    def get_entities(self):
        return self.entities_by_layer

    def draw_sidebar(self):
        """Draw the layer selection sidebar"""
        pygame.draw.rect(self.screen, constants.LIGHT_GRAY, 
                        (constants.DRAWING_AREA_WIDTH, 0, constants.SIDEBAR_WIDTH, constants.SCREEN_HEIGHT))

        title = self.font.render("Layers", True, constants.BLACK)
        self.screen.blit(title, (constants.DRAWING_AREA_WIDTH + 10, 10))

        select_all_rect = pygame.Rect(constants.DRAWING_AREA_WIDTH + 10, 40, 130, 30)
        deselect_all_rect = pygame.Rect(constants.DRAWING_AREA_WIDTH + 150, 40, 130, 30)

        pygame.draw.rect(self.screen, constants.GREEN, select_all_rect)
        pygame.draw.rect(self.screen, constants.RED, deselect_all_rect)

        select_text = self.small_font.render("Select All", True, constants.BLACK)
        deselect_text = self.small_font.render("Deselect All", True, constants.BLACK)
        self.screen.blit(select_text, (select_all_rect.x + 20, select_all_rect.y + 7))
        self.screen.blit(deselect_text, (deselect_all_rect.x + 15, deselect_all_rect.y + 7))

        y_offset = 90 - self.scroll_offset

        for layer in self.layers:
            if y_offset > constants.SCREEN_HEIGHT:
                break
            if y_offset < 40:
                y_offset += 30
                continue

            checkbox_rect = pygame.Rect(
                constants.DRAWING_AREA_WIDTH + self.checkbox_padding,
                y_offset,
                self.checkbox_size,
                self.checkbox_size
            )

            # Draw checkbox with layer color
            layer_color = self.layer_colors.get(layer, constants.WHITE)
            pygame.draw.rect(self.screen, layer_color, checkbox_rect)
            pygame.draw.rect(self.screen, constants.BLACK, checkbox_rect, 2)

            # Draw checkmark if selected
            if layer in self.selected_layers:
                # Draw black checkmark for better visibility
                pygame.draw.line(self.screen, constants.BLACK,
                               (checkbox_rect.x + 3, checkbox_rect.y + 10),
                               (checkbox_rect.x + 8, checkbox_rect.y + 15), 3)
                pygame.draw.line(self.screen, constants.BLACK,
                               (checkbox_rect.x + 8, checkbox_rect.y + 15),
                               (checkbox_rect.x + 17, checkbox_rect.y + 5), 3)

            # Draw layer name and entity count
            entity_count = len(self.entities_by_layer.get(layer, []))
            layer_text = self.small_font.render(
                f"{layer} ({entity_count})", 
                True, constants.BLACK
            )
            self.screen.blit(layer_text, 
                           (checkbox_rect.x + self.checkbox_size + 10, y_offset))

            y_offset += 30

        # Instructions
        inst_y = constants.SCREEN_HEIGHT - 100
        inst1 = self.small_font.render("Mouse: Pan (drag)", True, constants.BLACK)
        inst2 = self.small_font.render("Wheel: Zoom", True, constants.BLACK)
        inst3 = self.small_font.render("R: Reset view", True, constants.BLACK)
        inst4 = self.small_font.render("ESC: Exit", True, constants.BLACK)
        self.screen.blit(inst1, (constants.DRAWING_AREA_WIDTH + 10, inst_y))
        self.screen.blit(inst2, (constants.DRAWING_AREA_WIDTH + 10, inst_y + 20))
        self.screen.blit(inst3, (constants.DRAWING_AREA_WIDTH + 10, inst_y + 40))
        self.screen.blit(inst4, (constants.DRAWING_AREA_WIDTH + 10, inst_y + 60))

    def handle_click(self, pos):
        """Handle mouse click events"""
        x, y = pos

        if x > constants.DRAWING_AREA_WIDTH:
            if 40 <= y <= 70:
                if constants.DRAWING_AREA_WIDTH + 10 <= x <= constants.DRAWING_AREA_WIDTH + 140:
                    self.selected_layers = set(self.layers)
                    return
                elif constants.DRAWING_AREA_WIDTH + 150 <= x <= constants.DRAWING_AREA_WIDTH + 280:
                    self.selected_layers.clear()
                    return

            y_offset = 90 - self.scroll_offset
            for layer in self.layers:
                if y_offset > constants.SCREEN_HEIGHT:
                    break
                if y_offset < 40:
                    y_offset += 30
                    continue

                checkbox_rect = pygame.Rect(
                    constants.DRAWING_AREA_WIDTH + self.checkbox_padding,
                    y_offset,
                    self.checkbox_size + 250,
                    self.checkbox_size
                )

                if checkbox_rect.collidepoint(x, y):
                    if layer in self.selected_layers:
                        self.selected_layers.remove(layer)
                    else:
                        self.selected_layers.add(layer)
                    return

                y_offset += 30

    def run(self):
        """Main application loop"""
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if event.pos[0] > constants.DRAWING_AREA_WIDTH:
                            self.handle_click(event.pos)
                        else:
                            self.dragging = True
                            self.last_mouse_pos = event.pos
                    elif event.button == 4:
                        if event.pos[0] > constants.DRAWING_AREA_WIDTH:
                            self.scroll_offset = max(0, self.scroll_offset - 20)
                        else:
                            self.scale *= 1.1
                    elif event.button == 5:
                        if event.pos[0] > constants.DRAWING_AREA_WIDTH:
                            self.scroll_offset += 20
                        else:
                            self.scale *= 0.9

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragging = False

                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        dx = event.pos[0] - self.last_mouse_pos[0]
                        dy = event.pos[1] - self.last_mouse_pos[1]
                        self.offset_x += dx
                        self.offset_y += dy
                        self.last_mouse_pos = event.pos

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.auto_fit_view()
                    elif event.key == pygame.K_ESCAPE:
                        running = False

            self.screen.fill(constants.BLACK)

            for layer in self.selected_layers:
                for entity in self.entities_by_layer.get(layer, []):
                    self.draw_entity(entity)

            self.draw_sidebar()

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

