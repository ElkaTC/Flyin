import pygame
import os
from parsing import MapParser, ParseError
from pathfinder import Pathfinder
from models import Graph

class Menu:
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
        category, name = os.path.split(map_path)
        clean_name, _ = os.path.splitext(name)
        clean_name = clean_name.replace('_', ' ').title()
        category = category.capitalize()
        parts = clean_name.split(' ', 1)
        if parts[0].isdigit() and len(parts) > 1:
            clean_name = f'{parts[0]} - {parts[1]}'
        return f'{category} {clean_name}'

    def draw(self) -> None:
        title = self.font.render("Choose a map", True, (255, 255, 255))
        self.screen.blit(title, (660, 40))
        start_y  = 220
        spacing = 60
        for i, name in enumerate(self.maps):
            color = (0, 0, 0)
            if i == self.selected:
                color = (200, 100, 0)
            display_name = self.map_name(name)
            text = self.font2.render(display_name, True, color)
            self.screen.blit(text, (120, start_y + i * spacing))
            
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_z):
                self.selected = (self.selected - 1) % len(self.maps)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % len(self.maps)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.chosen_map = os.path.join("maps", self.maps[self.selected])

class Renderer:
    def __init__(self) -> None:
        pygame.init()
        self.width = 1920
        self.height = 1080
        self.screen = pygame.display.set_mode(
            (self.width, self.height)
        )
        pygame.display.set_caption("Flyin")
        self.state = 'MENU'
        self.menu = Menu(self.screen)
        self.graph = None
        self.wallpaper = pygame.image.load('graphics/wallpaper.png').convert()
        self.wallpaper = pygame.transform.scale(
            self.wallpaper,
            (self.width, self.height))
        self.drone_sprite = pygame.image.load('graphics/drone.png').convert_alpha()
        self.drone_sprite = pygame.transform.scale(self.drone_sprite, (116, 116))
        self.running = True
        self.drone_visual_positions = {}
        
    def run(self) -> None:
        clock = pygame.time.Clock()
        last_step_time = pygame.time.get_ticks()
        step_interval = 400
        self.game_started = False
        self.game_keyboard = None
        while self.running:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if self.state == 'GAME':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.game_started = True
                            last_step_time = pygame.time.get_ticks()
                        elif event.key == pygame.K_RIGHT:
                            self.graph.step()
                            last_step_time = now
                if self.state == 'MENU':
                    self.menu.handle_event(event)
                    if self.menu.chosen_map:
                        try:
                            parser = MapParser(self.menu.chosen_map)
                            settings = parser.parse()
                            self.graph = Graph.from_settings(settings, parser.nb_drones)
                            start = self.graph.get_start_area()
                            end = self.graph.get_end_area()
                            pathfinder = Pathfinder()
                            for drone in self.graph.drones:
                                try:
                                    path, timetable = pathfinder.find_path(self.graph, start, end)
                                except:
                                    raise ParseError("No path finded")
                                drone.path = path[1:]
                                drone.timetable = timetable
                            self.state = 'GAME'
                        except ParseError as e:
                            print(e)
                            self.running = False
            self.screen.blit(self.wallpaper, (0, 0))
            if self.state == 'GAME':
                if self.game_started:
                    if now - last_step_time >= step_interval:
                        self.graph.step()
                        last_step_time = now
                    else:
                        pass
            if self.state == 'MENU':
                self.menu.draw()
            elif self.state == 'GAME':
                self.draw_connections()
                self.draw_areas()
                self.draw_drones()
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()

    def draw_areas(self) -> None:
        offset_x, offset_y = self.get_offset()
        for area in self.graph.areas.values():
            x = area.pos[0] * 75 + offset_x
            y = area.pos[1] * 75 + offset_y
            pygame.draw.circle(self.screen, (255, 255, 255), (x, y), 25)
        
    def draw_connections(self) -> None:
        offset_x, offset_y = self.get_offset()
        for connection in self.graph.connections:
            x1, y1 = connection.area1.pos
            x2, y2 = connection.area2.pos
            pygame.draw.line(
                self.screen,
                (0, 128, 0),
                (x1 * 75 + offset_x, y1 * 75 + offset_y),
                (x2 * 75 + offset_x, y2 * 75 + offset_y),
                3
            )
            
    def draw_drones(self):
        offset_x, offset_y = self.get_offset()
        for drone in self.graph.drones:
            if drone.current_connection:
                if drone.current_connection.area1 == drone.target_area:
                    start_area = drone.current_connection.area2
                else:
                    start_area = drone.current_connection.area1
                total_cost = drone.current_connection.cost_to(drone.target_area)
                progress = drone.travel_progress / total_cost if total_cost > 0 else 1.0
                raw_x = start_area.pos[0] + (drone.target_area.pos[0] - start_area.pos[0]) * progress
                raw_y = start_area.pos[1] + (drone.target_area.pos[1] - start_area.pos[1]) * progress
            else:
                current_area = drone.current_area if drone.current_area else drone.final_destination
                raw_x, raw_y = current_area.pos if current_area else (0, 0)
            target_x = raw_x * 75 + offset_x
            target_y = raw_y * 75 + offset_y
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
        positions_x = [area.pos[0] for area in self.graph.areas.values()]
        positions_y = [area.pos[1] for area in self.graph.areas.values()]

        min_x, max_x = min(positions_x), max(positions_x)
        min_y, max_y = min(positions_y), max(positions_y)

        scale = 75
        map_width = (max_x - min_x) * scale
        map_height = (max_y - min_y) * scale

        offset_x = (self.width - map_width) // 2
        offset_y = (self.height - map_height) // 2
        return offset_x, offset_y