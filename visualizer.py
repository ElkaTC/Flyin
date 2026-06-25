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
        
    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            self.screen.fill((30, 30, 30))
            self.graph.step()
            pygame.time.delay(300)
            self.draw_connections()
            self.draw_areas()
            self.draw_drones()
            pygame.display.flip()
        pygame.quit()

    def draw_areas(self) -> None:
        offset_x, offset_y = self.get_offset()
        for area in self.graph.areas.values():
            x = area.pos[0] * 70 + offset_x
            y = area.pos[1] * 70 + offset_y
            pygame.draw.circle(
                self.screen,
                (255, 255, 255),
                (x, y),
                20
            )
        
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
            
    def draw_drones(self) -> None:
        offset_x, offset_y = self.get_offset()
        for drone in self.graph.drones:
                x = drone.current_area.pos[0] * 70 + offset_x
                y = drone.current_area.pos[1] * 70 + offset_y

                pygame.draw.circle(
                    self.screen,
                    (255, 0, 0),
                    (x, y),
                    6
                )
    def get_offset(self) -> tuple[int, int]:

        positions_x = [area.pos[0] for area in self.graph.areas.values()]
        positions_y = [area.pos[1] for area in self.graph.areas.values()]

        min_x = min(positions_x)
        max_x = max(positions_x)

        min_y = min(positions_y)
        max_y = max(positions_y)

        scale = 70

        map_width = (max_x - min_x) * scale
        map_height = (max_y - min_y) * scale

        offset_x = (self.width - map_width) // 2
        offset_y = (self.height - map_height) // 2

        return offset_x, offset_y