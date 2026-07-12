from enum import Enum
from parsing import MapSetting
from typing import Dict, List, Optional, Tuple


class AreaType(Enum):
    """Enum representing the different types of zones
    impacting movement costs."""
    NORMAL = "normal"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"
    PRIORITY = "priority"


class Color(Enum):
    """Enum representing RGB color values for graphical display."""
    WHITE = (240, 240, 240)
    BLUE = (50, 150, 220)
    YELLOW = (240, 200, 60)
    CYAN = (50, 180, 185)
    LIME = (100, 210, 100)
    MAGENTA = (210, 80, 150)
    GREEN = (40, 165, 95)
    RED = (220, 70, 70)
    PURPLE = (130, 90, 170)
    BLACK = (30, 30, 30)
    BROWN = (155, 105, 75)
    ORANGE = (230, 125, 50)
    MAROON = (150, 60, 60)
    GOLD = (215, 175, 50)
    DARKRED = (160, 45, 45)
    CRIMSON = (195, 50, 80)
    VIOLET = (170, 125, 210)
    RAINBOW = (0, 0, 0)


class Area:
    """
    Represents a node (zone/hub) within the drone navigation graph.
    """
    def __init__(self,
                 area_id: str,
                 pos: Tuple[int, int],
                 role: str,
                 area_type: AreaType = AreaType.NORMAL,
                 color: Optional[str] = "none",
                 max_drones: int = 1) -> None:
        """Initialize a new area with its constraints and properties."""
        self.area_id = area_id
        self.pos = pos
        self.area_type = area_type
        self.role = role
        self.color = color
        self.max_drones = max_drones
        self.reserved: Dict[int, int] = {}

        self.connections: List['Connection'] = []
        self.current_drones: List['Drone'] = []

    @property
    def movement_cost(self) -> int:
        """Return the travel cost to enter
        this area (2 if restricted, 1 otherwise)."""
        if self.area_type == AreaType.RESTRICTED:
            return 2
        return 1

    @property
    def is_blocked(self) -> bool:
        """Check if the area is blocked for navigation."""
        return self.area_type == AreaType.BLOCKED

    @property
    def is_end(self) -> bool:
        """Check if the area is the final destination hub."""
        return self.role == "end_hub"


class Drone:
    """
    Represents a drone that navigates from a
    start area to an end area.
    """
    def __init__(self,
                 drone_id: str,
                 start: Area,
                 end: Area) -> None:
        """Initialize a drone with its start point, destination,
        and flight state."""
        self.drone_id = drone_id
        self.current_area: Optional[Area] = start
        self.end = end
        self.current_connection: Optional['Connection'] = None
        self.target_area: Optional[Area] = None
        self.travel_progress = 0
        self.is_arrived = False
        self.path: List[Area] = []
        self.timetable: Dict[Area, int] = {}


class Connection:
    """
    Represents a bidirectional link between two areas.
    """
    def __init__(self,
                 area1: Area,
                 area2: Area,
                 max_drones: int = 1) -> None:
        """Initialize a connection between two
        areas with a maximum drone capacity."""
        self.area1 = area1
        self.area2 = area2
        self.max_drones = max_drones

        self.current_drones: List['Drone'] = []
        self.reserved: Dict[int, int] = {}

    def get_dest(self, area: Area) -> Optional[Area]:
        """
        Return the destination area opposite to the provided area.
        Returns None if the provided area is not part of this connection.
        """
        if area == self.area1:
            return self.area2
        elif area == self.area2:
            return self.area1
        return None

    def cost_to(self, destination: Area) -> int:
        """Return the travel cost to reach the destination via this link."""
        return destination.movement_cost


class Graph:
    """
    Manages the overall infrastructure
    (areas, connections, drones) and time progression.
    """
    def __init__(self) -> None:
        """Initialize an empty graph with a trajectory manager (Pathfinder)."""
        from pathfinder import Pathfinder
        self.areas: Dict[str, Area] = {}
        self.connections: List[Connection] = []
        self.drones: List[Drone] = []
        self.pathfinder = Pathfinder()
        self.current_time = 0
        self.turn = 0

    def add_area(self, area: Area) -> None:
        """Add an area to the graph's area registry."""
        self.areas[area.area_id] = area

    def add_connection(self, connection: Connection) -> None:
        """Add a link to the graph and register
        it in both connected areas."""
        self.connections.append(connection)
        connection.area1.connections.append(connection)
        connection.area2.connections.append(connection)

    def get_start_area(self) -> Optional[Area]:
        """Find and return the area defined
        as the starting point ('start_hub')."""
        for area in self.areas.values():
            if area.role == 'start_hub':
                return area
        return None

    def get_end_area(self) -> Optional[Area]:
        """Find and return the area defined
        as the final destination ('end_hub')."""
        for area in self.areas.values():
            if area.role == "end_hub":
                return area
        return None

    def get_connection(self, area1: Area, area2: Area) -> Optional[Connection]:
        """
        Find and return the connection existing between area1 and area2.
        Returns None if no direct link exists.
        """
        for connection in area1.connections:
            if connection.get_dest(area1) == area2:
                return connection
        return None

    def is_finished(self) -> bool:
        """Check if all drones have physically completed their route."""
        return all(
            len(drone.path) == 0 and drone.current_connection is None 
            for drone in self.drones
        )

    def step(self) -> None:
        """
        Advance the simulation by one time unit.
        Handles drone departures based on their
        timetables and progress through connections.
        """
        self.current_time += 1
        if not self.is_finished():
            self.turn += 1
        for drone in self.drones:
            if drone.is_arrived:
                continue
            if not drone.current_connection and drone.path:
                next_area = drone.path[0]
                if drone.current_area is not None:
                    connection = self.get_connection(
                        drone.current_area, next_area
                    )
                    planned_departure = drone.timetable.get(
                        drone.current_area, 0
                    )
                    if self.current_time >= planned_departure:
                        drone.current_connection = connection
                        drone.target_area = next_area
                        drone.travel_progress = 0
                        drone.path.pop(0)
                        drone.current_area = None
            if drone.current_connection and drone.target_area is not None:
                drone.travel_progress += 1
                cost = drone.current_connection.cost_to(drone.target_area)
                if drone.travel_progress >= cost:
                    drone.current_area = drone.target_area
                    drone.current_connection = None
                    drone.travel_progress = 0
                    if drone.current_area == drone.end:
                        drone.is_arrived = True

    @classmethod
    def from_settings(cls, settings: MapSetting, nb_drones: int) -> 'Graph':
        """
        Factory method: Instantiate and configure a complete Graph
        from a MapSetting configuration object and a given number of drones.
        """
        graph = cls()
        for hubs in settings.HUBS:
            area = Area(
                area_id=hubs.NAME,
                pos=hubs.POS,
                role=hubs.ROLE,
                area_type=AreaType(hubs.TYPE),
                color=hubs.COLOR,
                max_drones=hubs.MAX_DRONE
            )
            graph.add_area(area)

        for connect in settings.CONNECTIONS:
            link = Connection(
                area1=graph.areas[connect.SOURCE],
                area2=graph.areas[connect.TARGET],
                max_drones=connect.MAX_LINK
            )
            graph.add_connection(link)

        start_area = graph.get_start_area()
        end_area = graph.get_end_area()
        if start_area is not None and end_area is not None:
            for i in range(1, nb_drones + 1):
                drone = Drone(f'D{i}', start_area, end_area)
                graph.drones.append(drone)
                start_area.current_drones.append(drone)
        return graph
