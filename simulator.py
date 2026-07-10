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

    def load_map(self, map_path: str) -> bool:
        """
        Loads the map file, initializes the graph, and calculates paths for all drones.
        
        :param map_path: The relative path to the map text file.
        :return: True if the map was loaded and parsed successfully, False otherwise.
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
        if self.graph and not self.graph.is_finished():
            self.graph.step()
            self.turn += 1

    def is_finished(self) -> bool:
        """
        Checks if the simulation has reached its end state.
        
        :return: True if the graph simulation is finished or uninitialized, False otherwise.
        """
        if self.graph:
            return self.graph.is_finished()
        return True

    def toggle_auto_mode(self) -> None:
        """Toggles between automatic simulation progression and manual controls."""
        if not self.is_finished():
            self.game_started = not self.game_started