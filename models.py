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
                 start: Area,
                 end: Area) -> None:
        self.drone_id = drone_id
        self.current_area = start
        self.end = end
        self.current_connection = None
        self.target_area = None
        self.travel_progress = 0
        self.is_arrived = False
        self.path = []
        self.timetable = {}
    
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
        self.current_time = 0
        
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
    
    def get_connection(self, area1: Area, area2: Area):
        for connection in area1.connections:
            if connection.get_dest(area1) == area2:
                return connection
        return None
        
    def step(self) -> None:
        self.current_time += 1
        for drone in self.drones:
            if drone.is_arrived:
                continue
            if drone.current_connection:
                drone.travel_progress += 1
                if drone.travel_progress >= drone.current_connection.cost_to(drone.target_area):
                    drone.current_area = drone.target_area
                    drone.current_connection = None
                    drone.travel_progress = 0
                    if drone.current_area == drone.end:
                        drone.is_arrived = True
            elif drone.path:
                next_area = drone.path[0]
                connection = self.get_connection(drone.current_area, next_area)
                planned_departure = drone.timetable.get(drone.current_area, 0)
                if self.current_time >= planned_departure:
                    drone.current_connection = connection
                    drone.target_area = next_area
                    drone.travel_progress = 0
                    drone.path.pop(0)
                    drone.current_area = None
                        
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
        end_area = graph.get_end_area()
        for i in range(1, nb_drones + 1):
            drone = Drone(f'D{i}', start_area, end_area)
            graph.drones.append(drone)
            start_area.current_drones.append(drone)
        
        return graph
