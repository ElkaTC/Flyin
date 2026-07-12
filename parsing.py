import os
from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import Dict, List, Literal, Optional, Set, Tuple, cast


class ParseError(Exception):
    """Exception raised for errors encountered
    during map configuration parsing."""
    pass


class AreaSetting(BaseModel):
    """
    Pydantic model representing the structural
    configuration of a single hub/area.
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
    Root configuration validator enforcing complete structural
    integrity of the parsed map.
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
        """Enforces hub name validity, role requirements,
        and unique layouts."""
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
        """Validates that all map connections point
        to existing hubs, avoid self-loops, and aren't duplicated."""
        hub_names = {hub.NAME for hub in self.HUBS}
        seen = set()
        for connect in self.CONNECTIONS:
            if connect.SOURCE not in hub_names:
                raise ValueError(f"Unknown source hub: {connect.SOURCE}")
            if connect.TARGET not in hub_names:
                raise ValueError(f"Unknown target hub: {connect.TARGET}")
            if connect.SOURCE == connect.TARGET:
                raise ValueError(
                    f"Hub cannot connect to itself: {connect.SOURCE}"
                )

            key = tuple(sorted([connect.SOURCE, connect.TARGET]))
            if key in seen:
                raise ValueError(
                    f"Duplicate connection: "
                    f"{connect.SOURCE}-{connect.TARGET}"
                )
            seen.add(key)

    def _validate_path(self) -> None:
        """Uses DFS to guarantee a continuous
        traversal path exists between start and end hubs."""
        graph: Dict[str, List[str]] = {}
        for connect in self.CONNECTIONS:
            graph.setdefault(connect.SOURCE, []).append(connect.TARGET)
            graph.setdefault(connect.TARGET, []).append(connect.SOURCE)

        start_hub = next(
            hub.NAME for hub in self.HUBS if hub.ROLE == "start_hub"
        )
        end_hub = next(
            hub.NAME for hub in self.HUBS if hub.ROLE == "end_hub"
        )

        visited: Set[str] = set()
        stack: List[str] = [start_hub]

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
        self.nb_drones_init: bool = False
        self.nb_drones: int = 0

    def _create_area(
        self, value: str, role: Literal['start_hub', 'hub', 'end_hub'], line_number: int
    ) -> AreaSetting:
        from models import Color
        """
        Parses a textual line representing a hub definition.
        """
        if ('[' in value or ']' in value) and (value.count('[') != 1 or value.count(']') != 1 or value.index('[') > value.index(']')):
            raise ParseError(f"Line {line_number}: Invalid brackets structure")

        if '[' in value and ']' in value:
            if not value.strip().endswith(']'):
                raise ParseError(f"Line {line_number}: Unexpected text found after the closing bracket")

            mandatory, optional_str = value.split('[', 1)
            parts = mandatory.split()
            if len(parts) < 3:
                raise ParseError(f"Line {line_number}: Missing mandatory hub fields (name, x, y)")
                
            name, x, y = parts[0], parts[1], parts[2]
            area = AreaSetting(
                NAME=name,
                ROLE=role,
                POS=(int(x), int(y))
            )
            
            optional_str = optional_str.strip().rstrip(']')
            clean_optional = optional_str.split()
            options: List[Tuple[str, str]] = []
            
            for item in clean_optional:
                if '=' not in item:
                    raise ParseError(f"Line {line_number}: Malformed option '{item}', missing '='")
                name_opt, value_opt = item.split('=', 1)
                options.append((name_opt.strip(), value_opt.strip()))
                
            names_opt = [name_opt for name_opt, _ in options]
            if len(names_opt) != len(set(names_opt)):
                raise ParseError(f"Line {line_number}: Optional setting must be unique")

            for name_opt, value_opt in options:
                if name_opt == 'color':
                    color_upper = value_opt.upper()
                    if color_upper not in Color.__members__:
                        available_colors = ", ".join(Color.__members__.keys())
                        raise ParseError(
                            f"Line {line_number}: Invalid color '{value_opt}'. "
                            f"Supported colors are: {available_colors}"
                        )
                    area.COLOR = color_upper
                elif name_opt == 'zone':
                    if value_opt in ("normal", "blocked", "restricted", "priority"):
                        area.TYPE = cast(Literal["normal", "blocked", "restricted", "priority"], value_opt)
                    else:
                        raise ParseError(f"Line {line_number}: Invalid zone type '{value_opt}'")
                elif name_opt == 'max_drones':
                    val_int = int(value_opt)
                    if val_int <= 0:
                        raise ParseError(f"Line {line_number}: Invalid max_drones value '{value_opt}'. Must be > 0.")
                    area.MAX_DRONE = val_int
                else:
                    raise ParseError(f"Line {line_number}: Unknown area option '{name_opt}'")
            return area

        parts_simple = value.split()
        if len(parts_simple) < 3:
            raise ParseError(f"Line {line_number}: Missing mandatory hub fields (name, x, y)")
        name_s, x_s, y_s = parts_simple[0], parts_simple[1], parts_simple[2]
        return AreaSetting(
            NAME=name_s,
            ROLE=role,
            POS=(int(x_s), int(y_s))
        )

    def _create_connect(self, value: str, line_number: int) -> ConnectSetting:
        """
        Parses a textual line representing a network connection.
        """
        if ('[' in value or ']' in value) and (value.count('[') != 1 or value.count(']') != 1 or value.index('[') > value.index(']')):
            raise ParseError(f"Line {line_number}: Invalid brackets structure")

        if '[' in value and ']' in value:
            if not value.strip().endswith(']'):
                raise ParseError(f"Line {line_number}: Unexpected text found after the closing bracket")

            mandatory, optional = value.split('[', 1)
            if '-' not in mandatory:
                raise ParseError(f"Line {line_number}: Missing '-' splitter in connection")
            area1, area2 = mandatory.split('-', 1)
            connect = ConnectSetting(
                SOURCE=area1.strip(),
                TARGET=area2.strip()
            )
            
            optional = optional.strip().rstrip(']')
            if '=' not in optional:
                raise ParseError(f"Line {line_number}: Malformed option '{optional}', missing '='")
            name_opt, value_opt = optional.split('=', 1)
            if name_opt.strip() != 'max_link_capacity':
                raise ParseError(f"Line {line_number}: Unknown connection option '{name_opt}'")
            connect.MAX_LINK = int(value_opt)
            return connect

        if '-' not in value:
            raise ParseError(f"Line {line_number}: Missing '-' splitter in connection")
        area1, area2 = value.split('-', 1)
        return ConnectSetting(
            SOURCE=area1.strip(),
            TARGET=area2.strip()
        )

    def parse(self) -> MapSetting:
        """
        Reads, deserializes, and verifies raw configurations from the text file.
        """
        try:
            if not os.path.exists(self.filename):
                raise ParseError(f"File not found: {self.filename}")

            with open(self.filename, 'r') as file:
                for line_number, line in enumerate(file, start=1):
                    line = line.split('#', 1)[0].strip()
                    if not line or line.startswith('#'):
                        continue
                    if ':' not in line:
                        raise ParseError(f"Line {line_number}: Missing ':' separator")

                    data_type, value = line.split(':', 1)
                    data_type = data_type.strip()
                    value = value.strip()

                    if not self.nb_drones_init and data_type != 'nb_drones':
                        raise ParseError(f"Line {line_number}: 'nb_drones' must be defined on the first active line")

                    if data_type == 'nb_drones':
                        if self.nb_drones_init:
                            raise ParseError(f"Line {line_number}: 'nb_drones' is already defined")
                        try:
                            val = int(value)
                            if val <= 0:
                                raise ValueError()
                        except ValueError:
                            raise ParseError(f"Line {line_number}: 'nb_drones' must be an integer greater than 0")
                        self.nb_drones = int(value)
                        self.nb_drones_init = True
                    elif data_type in ('start_hub', 'hub', 'end_hub'):
                        role_literal: Literal['start_hub', 'hub', 'end_hub'] = data_type  # type: ignore[assignment]
                        self.areas.append(
                            self._create_area(value, role_literal, line_number)
                        )
                    elif data_type == 'connection':
                        connect = self._create_connect(value, line_number)
                        existing_hubs = {area.NAME for area in self.areas}
                        if connect.SOURCE not in existing_hubs:
                            raise ParseError(f"Line {line_number}: Unknown source hub '{connect.SOURCE}'")
                        if connect.TARGET not in existing_hubs:
                            raise ParseError(f"Line {line_number}: Unknown target hub '{connect.TARGET}'")
                        self.connections.append(connect)
                    else:
                        raise ParseError(f"Line {line_number}: Unknown field header '{data_type}'")

            if len(self.areas) < 2:
                raise ParseError("Map structural error: Must contain at least 2 hubs")
            if not self.connections:
                raise ParseError("Map structural error: Must contain at least 1 connection")

            return MapSetting(
                NB_DRONE=self.nb_drones,
                HUBS=self.areas,
                CONNECTIONS=self.connections
            )

        except ParseError:
            raise
        except (ValueError, IndexError, OSError, ValidationError) as err:
            raise ParseError(f"File parsing structural failure: {err}")
