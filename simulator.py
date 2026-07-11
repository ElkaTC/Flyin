import os
from parsing import MapParser, ParseError
from pathfinder import Pathfinder
from models import Graph

class Simulator:
    """
    Handles the core simulation logic, including map loading, pathfinding,
    and turn-by-turn progression, completely independent of the UI.
    """
    def __init__(self):
        self.graph = None
        self.game_started = False
        self.turn = 0
        self.flag = None

    def load_map(self, map_path: str) -> bool:
        """
        Loads the map file, initializes the graph, and calculates paths for all drones.
        
        param map_path: The relative path to the map text file.
        return: True if the map was loaded and parsed successfully, False otherwise.
        """
        try:
            parser = MapParser(map_path)
            settings = parser.parse()
            self.graph = Graph.from_settings(settings, parser.nb_drones)
            
            start = self.graph.get_start_area()
            end = self.graph.get_end_area()
            pathfinder = Pathfinder()
            
            for drone in self.graph.drones:
                try:
                    path, timetable = pathfinder.find_path(self.graph, start, end)
                except Exception:
                    raise ParseError("No path found")
                drone.path = path[1:]
                drone.timetable = timetable
                
            self.turn = 0
            self.game_started = False
            return True
        except ParseError as e:
            print(f"Parsing error: {e}")
            return False

    def step(self) -> None:
        """Advances the simulation by one turn if it is not yet finished."""
        if not self.graph or self.graph.is_finished():
            return
        drone_pos = ''
        print(f'\n-- Turn {self.turn} --')
        for drone in self.graph.drones:
            if drone.current_area:
                drone_pos += f'{drone.drone_id}-{drone.current_area.area_id} '
            elif drone.current_connection:
                c = drone.current_connection
                drone_pos += f'{drone.drone_id}-{c.area1.area_id} -> {c.area2.area_id} '
        # print('--------------')
        print(drone_pos)
        # print('--------------')
        self.graph.step()
        self.turn += 1
        if self.flag == 'debug':
            displayed_connections = set()
            for area in self.graph.areas.values():
                nb_drones = sum(1 for drone in self.graph.drones if drone.current_area == area and drone.current_connection is None)
                cap_text = f'{nb_drones}/{area.max_drones}' if area.role == 'hub' else f'{nb_drones}/{len(self.graph.drones)}'
                print(f'[Area] {area.area_id} - {cap_text}')
                for connection in area.connections:
                    if connection in displayed_connections:
                        continue
                    nb_drones_connect = sum(1 for drone in self.graph.drones if drone.current_connection == connection)
                    start = connection.area1
                    end = connection.area2
                    print(f'[Connection] {start.area_id} -> {end.area_id} - {nb_drones_connect}/{connection.max_drones}')
                    displayed_connections.add(connection)
        if self.graph.is_finished():
            print(f'\n-- Turn {self.turn} --')
            drone_pos = ''
            for drone in self.graph.drones:
                drone_pos += f'{drone.drone_id}-{drone.current_area.area_id} '
            print(drone_pos)
            print(f"\n-- Simulation Finished at Turn {self.turn} --")

    def is_finished(self) -> bool:
        """
        Checks if the simulation has reached its end state.
        
        return: True if the graph simulation is finished or uninitialized, False otherwise.
        """
        if self.graph:
            return self.graph.is_finished()
        return True

    def toggle_auto_mode(self) -> None:
        """Toggles between automatic simulation progression and manual controls."""
        if not self.is_finished():
            self.game_started = not self.game_started