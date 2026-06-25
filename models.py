from enum import Enum
from parsing import MapSetting

class AreaType(Enum):
    NORMAL = "normal"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"
    PRIORITY = "priority"


class Area:
    def __init__(self,
                 area_id: str, 
                 pos: tuple[int, int], 
                 role: str,
                 area_type: AreaType = AreaType.NORMAL,
                 color: str = "none",
                 max_drones: int = 1) -> None:
        self.area_id = area_id
        self.pos = pos
        self.area_type = area_type
        self.role = role
        self.color = color
        self.max_drones = max_drones
        self.reserved: dict[int, int] = {}
        
        self.connections: list['Connection'] = []
        self.current_drones: list['Drone'] = []
    
    @property
    def movement_cost(self) -> int:
        if self.area_type == AreaType.RESTRICTED:
            return 2
        return 1

    @property
    def is_blocked(self) -> bool:
        return self.area_type == AreaType.BLOCKED
    
    @property
    def is_priority(self) -> bool:
        return self.area_type == AreaType.PRIORITY
    
    @property
    def is_restricted(self) -> bool:
        return self.area_type == AreaType.RESTRICTED
    
    @property
    def is_end(self):
        return self.role == "end_hub"

class Drone:
    def __init__(self,
                 drone_id: int,
                 start: Area) -> None:
        self.drone_id = drone_id
        self.current_area = start
        
        self.path: list['Area'] = []
        self.path_index: int = 0
        self.finished: bool = False
        self.target_area: Area | None = None
        
        self.in_transit = False
        self.remaining_turns = 0
        self.next_area: Area | None = None
        self.on_connection: Connection | None = None
        start.current_drones.append(self)
    
    def step(self) -> None:
        pass
            

class Connection:
    def __init__(self,
                 area1: Area,
                 area2: Area,
                 max_drones: int = 1) -> None:
        self.area1 = area1
        self.area2 = area2
        self.max_drones = max_drones
        
        self.current_drones: list['Drone'] = []
        self.reserved: dict[int, int] = {}
        
    def get_dest(self, area: Area) -> Area:
        if area == self.area1:
            return self.area2
        return None
    
    def cost_to(self, destination: Area) -> int:
        return destination.movement_cost

class Graph:
    def __init__(self) -> None:
        from pathfinder import Pathfinder
        self.areas: dict[str, Area] = {}
        self.connections: list[Connection] = []
        self.drones: list[Drone] = []
        self.pathfinder = Pathfinder()
        
    def add_area(self, area: Area) -> None:
        self.areas[area.area_id] = area

    def add_connection(self, connection: Connection) -> None:
        self.connections.append(connection)
        connection.area1.connections.append(connection)
        connection.area2.connections.append(connection)
        
    def get_neighbors(self, area: Area) -> list[Area]:
        return [connection.get_dest(area) for connection in area.connections]
    
    def get_start_area(self) -> Area:
        for area in self.areas.values():
            if area.role == 'start_hub':
                return area
            
    def get_end_area(self) -> Area:
        for area in self.areas.values():
            if area.role == "end_hub":
                return area
        
    def step(self) -> None:
        for drone in self.drones:
            if drone.finished:
                continue
            if drone.in_transit:
                drone.remaining_turns -= 1
                if drone.remaining_turns <= 0:
                    if drone.on_connection:
                        drone.on_connection.current_drones.remove(drone)
                    drone.in_transit = False
                    drone.current_area = drone.next_area
                    if drone.current_area.is_end:
                        drone.finished = True
                    drone.current_area.current_drones.append(drone)
                    drone.next_area = None
                    drone.on_connection = None
            else:
                path = self.pathfinder.find_path(
                    self,
                    drone.current_area,
                    self.get_end_area()
                )
                if len(path) < 2:
                    continue
                next_area = path[1]
                connection = None
                for c in drone.current_area.connections:
                    if c.get_dest(drone.current_area) == next_area:
                        connection = c
                        break
                if connection is None:
                    continue
                if len(connection.current_drones) >= connection.max_drones:
                    continue
                drone.current_area.current_drones.remove(drone)
                connection.current_drones.append(drone)
                drone.in_transit = True
                drone.next_area = next_area
                drone.on_connection = connection
                drone.remaining_turns = connection.cost_to(next_area)
                        
    @classmethod
    def from_settings(cls, settings: MapSetting, nb_drones: int) -> 'Graph':
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
        for i in range(1, nb_drones + 1):
            drone = Drone(f'D{i}', start_area)
            graph.drones.append(drone)
            start_area.current_drones.append(drone)
        
        return graph
