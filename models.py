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
        
    def set_path(self, path: list['Area']) -> None:
        self.path = path
        self.path_index = 0
        self.current_area = path[0]
        self.finished = False
    
    def step(self) -> None:
        if self.finished or not self.path:
            return
        if self.path_index >= len(self.path) - 1:
            self.finished = True
            return
        next_area = self.path[self.path_index + 1]
        if not next_area.is_end and len(next_area.current_drones) >= next_area.max_drones:
            return
        self.current_area.current_drones.remove(self)
        self.path_index += 1
        self.current_area = next_area
        next_area.current_drones.append(self)

class Connection:
    def __init__(self,
                 area1: Area,
                 area2: Area,
                 max_drones: int = 1) -> None:
        self.area1 = area1
        self.area2 = area2
        self.max_drones = max_drones
        
        self.current_drones: list['Drone'] = []
        
    def get_dest(self, area: Area) -> Area:
        return self.area2 if area == self.area1 else self.area1
    
    def cost_to(self, destination: Area) -> int:
        return destination.movement_cost

class Graph:
    def __init__(self) -> None:
        self.areas: dict[str, Area] = {}
        self.connections: list[Connection] = []
        self.drones: list[Drone] = []
        
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
            drone.step()
    
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
