import pygame
import os
from models import Color
from simulator import Simulator

class Menu:
    """Handles the map selection menu, including file discovery and user input."""
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font = pygame.font.Font('graphics/colinoosh.otf', 50)
        self.font2 = pygame.font.Font('graphics/Study Daily.otf', 50)
        self.categories = ["easy", "medium", "hard", "challenger"]
        self.maps = []
        
        for cat in self.categories:
            path = os.path.join("maps", cat)
            if os.path.exists(path):
                for f in sorted(os.listdir(path)):
                    if f.endswith(".txt"):
                        self.maps.append(os.path.join(cat, f))
        self.selected = 0
        self.chosen_map = None
        
    def map_name(self, map_path: str) -> str:
        """Formats the raw map file path into a clean, human-readable display string."""
        category, name = os.path.split(map_path)
        clean_name, _ = os.path.splitext(name)
        clean_name = clean_name.replace('_', ' ').title()
        category = category.capitalize()
        parts = clean_name.split(' ', 1)
        if parts[0].isdigit() and len(parts) > 1:
            clean_name = f'{parts[0]} - {parts[1]}'
        return f'{category} {clean_name}'

    def draw(self) -> None:
        """Renders the menu interface and map list onto the screen."""
        title = self.font.render("Choose a map", True, (255, 255, 255))
        self.screen.blit(title, (700, 30))
        start_y = 220
        spacing = 60
        for i, name in enumerate(self.maps):
            color = (0, 0, 0)
            if i == self.selected:
                color = (220, 100, 0)
            display_name = self.map_name(name)
            text = self.font2.render(display_name, True, color)
            self.screen.blit(text, (120, start_y + i * spacing))
            
    def handle_event(self, event: pygame.event.Event) -> None:
        """Processes keyboard navigation events for the menu."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_z):
                self.selected = (self.selected - 1) % len(self.maps)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.maps)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.chosen_map = os.path.join("maps", self.maps[self.selected])


class Renderer:
    """Manages the Pygame window context, graphics rendering, and the main game loop."""
    def __init__(self, default_map: str = None) -> None:
        pygame.init()
        self.width = 1920
        self.height = 1080
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Flyin")
        
        self.state = 'MENU'
        self.menu = Menu(self.screen)
        self.simulator = Simulator()
        
        if default_map:
            success = self.simulator.load_map(default_map)
            if success:
                self.state = 'GAME'
                self.menu.chosen_map = default_map  # Optionnel, pour garder la référence
            else:
                print(f"Erreur : Impossible de charger la carte '{default_map}'")
                pygame.quit()
                sys.exit(1)
        
        self.wallpaper = pygame.image.load('graphics/wallpaper.png').convert()
        self.wallpaper = pygame.transform.scale(self.wallpaper, (self.width, self.height))
        self.wallpaper_menu = pygame.image.load('graphics/wallpaper_menu.png').convert()
        self.wallpaper_menu = pygame.transform.scale(self.wallpaper_menu, (self.width, self.height))
        self.drone_sprite = pygame.image.load('graphics/drone.png').convert_alpha()
        self.drone_sprite = pygame.transform.scale(self.drone_sprite, (111, 111))
        self.stats_font = pygame.font.Font('graphics/Kids_Word.otf', 20)
        
        self.running = True
        self.drone_visual_positions = {}
        
    def run(self) -> None:
        """Starts the main Pygame execution loop."""
        clock = pygame.time.Clock()
        last_step_time = pygame.time.get_ticks()
        step_interval = 400
        
        while self.running:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    
                if self.state == 'GAME':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.simulator.toggle_auto_mode()
                            last_step_time = pygame.time.get_ticks()
                        elif event.key == pygame.K_RIGHT and not self.simulator.game_started:
                            self.simulator.step()
                            last_step_time = now 
                        elif event.key == pygame.K_ESCAPE:
                            self.state = 'MENU'
                            self.simulator.game_started = False
                            self.menu.chosen_map = None
                        elif event.key == pygame.K_LEFT and not self.simulator.game_started:
                            self.simulator.load_map(self.menu.chosen_map)
                            last_step_time = pygame.time.get_ticks()
                            
                elif self.state == 'MENU':
                    self.menu.handle_event(event)
                    if self.menu.chosen_map:
                        success = self.simulator.load_map(self.menu.chosen_map)
                        if success:
                            self.state = 'GAME'
                        else:
                            self.running = False

            if self.state == 'GAME' and self.simulator.game_started:
                if now - last_step_time >= step_interval:
                    self.simulator.step()
                    last_step_time = now
                    if self.simulator.is_finished():
                        self.simulator.game_started = False

            if self.state == 'MENU':
                self.screen.blit(self.wallpaper_menu, (0, 0))
                self.menu.draw()
            elif self.state == 'GAME':
                self.screen.blit(self.wallpaper, (0, 0))
                
                text_turn = self.menu.font.render(f"Turn : {self.simulator.graph.turn}", True, (255, 255, 255))
                self.screen.blit(text_turn, (1550, 30))
                
                state_text = 'Auto' if self.simulator.game_started else 'Manual'
                text_mode = self.menu.font.render(f"Mode : {state_text}", True, (255, 255, 255))
                self.screen.blit(text_mode, (700, 30))
                
                self.draw_connections()
                self.draw_areas()
                self.draw_drones()
                
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()

    def draw_areas(self) -> None:
        """Renders map nodes/hubs along with their occupancy ratios."""
        offset_x, offset_y = self.get_offset()
        graph = self.simulator.graph
        for area in graph.areas.values():
            x = area.pos[0] * 75 + offset_x
            y = area.pos[1] * 120 + offset_y
            if area.color == 'none':
                draw_color = Color.GREEN if area.role == 'start_hub' else (Color.RED if area.role == 'end_hub' else Color.WHITE)
            else:
                draw_color = Color[area.color]  
                
            if area.color == 'RAINBOW':
                pygame.draw.circle(self.screen, Color.PURPLE.value, (x, y), 30)
                pygame.draw.circle(self.screen, Color.BLUE.value, (x, y), 26)
                pygame.draw.circle(self.screen, Color.GREEN.value, (x, y), 22)
                pygame.draw.circle(self.screen, Color.LIME.value, (x, y), 18)
                pygame.draw.circle(self.screen, Color.YELLOW.value, (x, y), 14)
                pygame.draw.circle(self.screen, Color.ORANGE.value, (x, y), 10)
            else:
                pygame.draw.circle(self.screen, draw_color.value, (x, y), 30)
                pygame.draw.circle(self.screen, Color.WHITE.value, (x, y), 23)
                
            nb_drones = sum(1 for drone in graph.drones if drone.current_area == area and drone.current_connection is None)
            cap_text = f'{nb_drones}/{area.max_drones}' if area.role == 'hub' else f'{nb_drones}/{len(graph.drones)}'
            
            text_surface = self.stats_font.render(cap_text, True, (0, 0, 0))
            text_rect = text_surface.get_rect(center=(x, y + 50))
            fond_rect = text_rect.inflate(8, 4)
            pygame.draw.rect(self.screen, Color.WHITE.value, fond_rect)
            self.screen.blit(text_surface, text_rect)
        
    def draw_connections(self) -> None:
        """Draws network connection links bridging graph nodes together."""
        offset_x, offset_y = self.get_offset()
        for connection in self.simulator.graph.connections:
            x1, y1 = connection.area1.pos
            x2, y2 = connection.area2.pos
            pygame.draw.line(
                self.screen,
                (0, 100, 0),
                (x1 * 75 + offset_x, y1 * 120 + offset_y),
                (x2 * 75 + offset_x, y2 * 120 + offset_y),
                4
            )
            
    def draw_drones(self) -> None:
        """Updates and draws drones using localized linear interpolation for smooth motion."""
        offset_x, offset_y = self.get_offset()
        for drone in self.simulator.graph.drones:
            if drone.current_connection:
                start_area = drone.current_connection.area2 if drone.current_connection.area1 == drone.target_area else drone.current_connection.area1
                total_cost = drone.current_connection.cost_to(drone.target_area)
                progress = drone.travel_progress / total_cost if total_cost > 0 else 1.0
                raw_x = start_area.pos[0] + (drone.target_area.pos[0] - start_area.pos[0]) * progress
                raw_y = start_area.pos[1] + (drone.target_area.pos[1] - start_area.pos[1]) * progress
            else:
                current_area = drone.current_area if drone.current_area else drone.final_destination
                raw_x, raw_y = current_area.pos if current_area else (0, 0)
                
            target_x = raw_x * 75 + offset_x
            target_y = raw_y * 120 + offset_y
            
            if drone not in self.drone_visual_positions:
                self.drone_visual_positions[drone] = [target_x, target_y]
            current_vis_x, current_vis_y = self.drone_visual_positions[drone]
            speed = 0.15
            new_vis_x = current_vis_x + (target_x - current_vis_x) * speed
            new_vis_y = current_vis_y + (target_y - current_vis_y) * speed
            self.drone_visual_positions[drone] = [new_vis_x, new_vis_y]
            
            rect = self.drone_sprite.get_rect(center=(int(new_vis_x), int(new_vis_y)))
            self.screen.blit(self.drone_sprite, rect)
            
    def get_offset(self) -> tuple[int, int]:
        """Calculates centering offsets based on extreme map coordinates to bound graphics onto the screen canvas."""
        positions_x = [area.pos[0] for area in self.simulator.graph.areas.values()]
        positions_y = [area.pos[1] for area in self.simulator.graph.areas.values()]

        min_x, max_x = min(positions_x), max(positions_x)
        min_y, max_y = min(positions_y), max(positions_y)

        scale = 75
        map_width = (max_x - min_x) * scale
        map_height = (max_y - min_y) * scale

        offset_x = (self.width - map_width) // 2
        offset_y = (self.height - map_height) // 2
        return offset_x, offset_y