import pygame
from models import Graph

class Renderer:
    def __init__(self, graph: Graph) -> None:
        pygame.init()

        self.graph = graph
        self.width = 1920
        self.height = 1080
        self.screen = pygame.display.set_mode(
            (self.width, self.height)
        )
        pygame.display.set_caption("Flyin")
        self.running = True
        self.drone_visual_positions = {}
        
    def run(self) -> None:
        clock = pygame.time.Clock()
        last_step_time = pygame.time.get_ticks()
        step_interval = 400
        while self.running:
            now = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            if now - last_step_time >= step_interval:
                self.graph.step()
                last_step_time = now
            self.screen.fill((30, 30, 30))
            self.draw_connections()
            self.draw_areas()
            self.draw_drones()
            pygame.display.flip()
            clock.tick(60)
        pygame.quit()

    def draw_areas(self) -> None:
        offset_x, offset_y = self.get_offset()
        for area in self.graph.areas.values():
            x = area.pos[0] * 70 + offset_x
            y = area.pos[1] * 70 + offset_y
            pygame.draw.circle(self.screen, (255, 255, 255), (x, y), 20)
        
    def draw_connections(self) -> None:
        offset_x, offset_y = self.get_offset()
        for connection in self.graph.connections:
            x1, y1 = connection.area1.pos
            x2, y2 = connection.area2.pos
            pygame.draw.line(
                self.screen,
                (0, 128, 0),
                (x1 * 70 + offset_x, y1 * 70 + offset_y),
                (x2 * 70 + offset_x, y2 * 70 + offset_y),
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
            target_x = raw_x * 70 + offset_x
            target_y = raw_y * 70 + offset_y
            if drone not in self.drone_visual_positions:
                self.drone_visual_positions[drone] = [target_x, target_y]
            current_vis_x, current_vis_y = self.drone_visual_positions[drone]
            speed = 0.15
            new_vis_x = current_vis_x + (target_x - current_vis_x) * speed
            new_vis_y = current_vis_y + (target_y - current_vis_y) * speed
            self.drone_visual_positions[drone] = [new_vis_x, new_vis_y]
            drone_color = (0, 255, 0) if drone.is_arrived else (255, 50, 50)
            pygame.draw.circle(self.screen, drone_color, (int(new_vis_x), int(new_vis_y)), 8)
            
    def get_offset(self) -> tuple[int, int]:
        positions_x = [area.pos[0] for area in self.graph.areas.values()]
        positions_y = [area.pos[1] for area in self.graph.areas.values()]

        min_x, max_x = min(positions_x), max(positions_x)
        min_y, max_y = min(positions_y), max(positions_y)

        scale = 70
        map_width = (max_x - min_x) * scale
        map_height = (max_y - min_y) * scale

        offset_x = (self.width - map_width) // 2
        offset_y = (self.height - map_height) // 2
        return offset_x, offset_y