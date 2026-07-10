from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import Optional, Literal

class ParseError(Exception):
    """Exception raised for errors encountered during map configuration parsing."""
    pass

class AreaSetting(BaseModel):
    """
    Pydantic model representing the structural configuration of a single hub/area.
    """
    NAME: str
    ROLE: Literal['start_hub', 'hub', 'end_hub']
    POS: tuple[int, int]
    COLOR: Optional[str] = 'none'
    TYPE: Literal["normal", "blocked", "restricted", "priority"] = "normal"
    MAX_DRONE: int = Field(default=1, gt=0)
    
class ConnectSetting(BaseModel):
    """
    Pydantic model representing the linkage between two structural hubs.
    """
    SOURCE: str
    TARGET: str
    MAX_LINK: int = Field(default=1, gt=0)

class MapSetting(BaseModel):
    """
    Root configuration validator enforcing complete structural integrity of the parsed map.
    """
    NB_DRONE: int = Field(gt=0)
    HUBS: list[AreaSetting]
    CONNECTIONS: list[ConnectSetting]

    @model_validator(mode="after")
    def validation_rules(self) -> 'MapSetting':
        """
        Runs comprehensive post-parsing checks covering hub uniqueness,
        connection bounds, and overall graph reachability.
        """
        self._validate_hubs()
        self._validate_connections()
        self._validate_path()
        return self
        
    def _validate_hubs(self) -> None:
        """Enforces hub name validity, role requirements, and unique layouts."""
        start_count = sum(hub.ROLE == "start_hub" for hub in self.HUBS)
        end_count = sum(hub.ROLE == "end_hub" for hub in self.HUBS)
        
        for hub in self.HUBS:
            if '-' in hub.NAME or ' ' in hub.NAME:
                raise ValueError(f"Invalid hub name: {hub.NAME}")
                
        if start_count != 1:
            raise ValueError("Map must contain exactly 1 start hub")
        if end_count != 1:
            raise ValueError("Map must contain exactly 1 end hub")
            
        list_names = [hub.NAME for hub in self.HUBS]
        if len(list_names) != len(set(list_names)):
            raise ValueError("Hub names must be unique")
            
        positions = [hub.POS for hub in self.HUBS]
        if len(positions) != len(set(positions)):
            raise ValueError("Hub positions must be unique")
            
        if not self.CONNECTIONS:
            raise ValueError("Map must contain at least one connection")
      
    def _validate_connections(self) -> None:            
        """Validates that all map connections point to existing hubs, avoid self-loops, and aren't duplicated."""
        hub_names = {hub.NAME for hub in self.HUBS}
        seen = set()
        for connect in self.CONNECTIONS:
            if connect.SOURCE not in hub_names:
                raise ValueError(f"Unknown source hub: {connect.SOURCE}")
            if connect.TARGET not in hub_names:
                raise ValueError(f"Unknown target hub: {connect.TARGET}")
            if connect.SOURCE == connect.TARGET:
                raise ValueError(f"Hub cannot connect to itself: {connect.SOURCE}")
                
            key = tuple(sorted([connect.SOURCE, connect.TARGET]))
            if key in seen:
                raise ValueError(f"Duplicate connection: {connect.SOURCE}-{connect.TARGET}")
            seen.add(key)
            
    def _validate_path(self) -> None:   
        """Uses DFS to guarantee a continuous traversal path exists between start and end hubs."""
        graph = {}
        for connect in self.CONNECTIONS:    
            graph.setdefault(connect.SOURCE, []).append(connect.TARGET)
            graph.setdefault(connect.TARGET, []).append(connect.SOURCE)
            
        start_hub = next(hub.NAME for hub in self.HUBS if hub.ROLE == "start_hub") 
        end_hub = next(hub.NAME for hub in self.HUBS if hub.ROLE == "end_hub")
        
        visited = set()
        stack = [start_hub]
        
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    stack.append(neighbor)
                    
        if end_hub not in visited:
            raise ValueError("No path exists between start hub and end hub")    


class MapParser:
    """
    Parser for handling text-based map definition configuration files.
    """
    def __init__(self, filename: str):
        """Initialize parser state with a target file path."""
        self.filename = filename
        self.areas: list[AreaSetting] = []
        self.connections: list[ConnectSetting] = []
        self.nb_drones: int = 0
        self.nb_drones_init = False

    def _create_area(self, value: str, role: str) -> AreaSetting:
        """
        Parses a textual line representing a hub definition.
        Handles base attributes alongside nested bracket properties like [color=X zone=Y].
        """
        if value.count('[') != value.count(']'):
            raise ParseError("Invalid brackets")
            
        if '[' in value and ']' in value:
            mandatory, optional = value.split('[', 1)
            name, x, y = mandatory.split()
            area = AreaSetting(
                NAME=name,
                ROLE=role,
                POS=(int(x), int(y))
            )
            optional = optional.strip('[]').split()
            options = []
            for item in optional:
                name_opt, value_opt = item.split('=', 1)
                options.append((name_opt.strip(), value_opt.strip()))
            names_opt = [name_opt for name_opt, _ in options]
            if len(names_opt) != len(set(names_opt)):
                raise ParseError("Optional setting must be unique")
                
            for name_opt, value_opt in options:
                if name_opt == 'color':
                    area.COLOR = value_opt.upper()
                elif name_opt == 'zone':
                    area.TYPE = value_opt
                elif name_opt == 'max_drones':
                    area.MAX_DRONE = int(value_opt)
                else:
                    raise ParseError(f"Unknown area option: {name_opt}")
            return area
        
        name, x, y = value.split()
        return AreaSetting(
            NAME=name,
            ROLE=role,
            POS=(int(x), int(y))
        )

    def _create_connect(self, value: str) -> ConnectSetting:
        """
        Parses a textual line representing a network connection.
        Handles structural linking formatting and max_link_capacity overrides.
        """
        if value.count('[') != value.count(']'):
            raise ParseError("Invalid brackets")
            
        if '[' in value and ']' in value:
            mandatory, optional = value.split('[', 1)
            area1, area2 = mandatory.split('-', 1)
            connect = ConnectSetting(
                SOURCE=area1.strip(),
                TARGET=area2.strip()
            )
            optional = optional.strip('[]')
            name_opt, value_opt = optional.split('=', 1)
            if name_opt != 'max_link_capacity':
                raise ParseError(f"Unknown connection option: {name_opt}")
            connect.MAX_LINK = int(value_opt)
            return connect

        area1, area2 = value.split('-', 1)
        return ConnectSetting(
            SOURCE=area1.strip(),
            TARGET=area2.strip()
        )

    def parse(self) -> MapSetting:
        """
        Reads, deserializes, and verifies raw configurations from the text file.
        Returns a verified MapSetting runtime object instance if configuration passes syntax/graph checks.
        """
        try:
            with open(self.filename, 'r') as file:
                for line_number, line in enumerate(file, start=1):
                    line = line.split('#', 1)[0].strip()
                    if not line or line.startswith('#'):
                        continue
                    if ':' not in line:
                        raise ParseError(f"Line {line_number}: Missing ':'")
                        
                    data_type, value = line.split(':', 1)
                    data_type = data_type.strip()
                    value = value.strip()
                    
                    if not self.nb_drones_init and data_type != 'nb_drones':
                        raise ParseError(
                            f"Line {line_number}: nb_drones must be the first line"
                        )
                        
                    if data_type == 'nb_drones':
                        if self.nb_drones_init:
                            raise ParseError(
                                f"Line {line_number}: nb_drones already defined"
                            )
                        self.nb_drones = int(value)
                        self.nb_drones_init = True
                    elif data_type in ('start_hub', 'hub', 'end_hub'):
                        self.areas.append(self._create_area(value, data_type))
                    elif data_type == 'connection':
                        connect = self._create_connect(value)
                        existing_hubs = {area.NAME for area in self.areas}
                        if connect.SOURCE not in existing_hubs:
                            raise ParseError(
                                f"Line {line_number}: Unknown source hub: {connect.SOURCE}"
                            )
                        if connect.TARGET not in existing_hubs:
                            raise ParseError(
                                f"Line {line_number}: Unknown target hub: {connect.TARGET}"
                            )
                        self.connections.append(connect)
                    else:
                        raise ParseError(f"Line {line_number}: Unknown field: {data_type}")
                        
            if len(self.areas) < 2:
                raise ParseError("Map must contain at least 2 hubs")
            if not self.connections:
                raise ParseError("Map must contain at least 1 connection")
                
            return MapSetting(
                NB_DRONE=self.nb_drones,
                HUBS=self.areas,
                CONNECTIONS=self.connections
            )

        except (ValueError, IndexError, OSError, ValidationError) as err:
            raise ParseError(f"File parsing failed: {err}")
