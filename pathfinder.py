import heapq

class Pathfinder:
    """
    A space-time pathfinding engine utilizing an A* variant over a time-extended graph.
    Computes conflict-free trajectories for multiple drones by taking resource 
    reservations (hubs and links) into account over time.
    """
    HORIZON = 200

    def find_path(self, graph, start, end):
        """
        Finds a conflict-free path and departure timetable from a start area to an end area.

        Uses a space-time expansion where states are defined as (Area, Arrival_Time). 
        Explores paths while respecting dynamic capacity constraints on both areas and 
        connections, tracking paths backward to register space-time resource reservations.

        Args:
            graph (Graph): The infrastructure network context.
            start (Area): The origin hub node.
            end (Area): The destination hub node.

        Returns:
            tuple[list[Area], dict[Area, int]]: A tuple containing:
                - path: A list of ordered Area objects representing the planned route.
                - timetable: A mapping of Area nodes to their scheduled departure turn.
            list: Returns an empty list if no valid, conflict-free path is found within the horizon bounds.
        """
        start_state = (start, 0)
        best = {start_state: 0}
        previous = {}
        counter = 0
        queue = [(0, counter, start_state)]
        visited = set()
        final_state = None
        
        while queue:
            _, _, state = heapq.heappop(queue)
            area, arrival = state
            
            if area is end:
                final_state = state
                break
                
            if state in visited:
                continue
            visited.add(state)
            
            # Explore waiting in the current area up to the predefined time horizon limits
            for departure in range(arrival + 1, arrival + 1 + self.HORIZON):
                if not self._area_free(area, departure - 1):
                    break  # Area is congested/blocked; waiting further is impossible
                    
                for connection in area.connections:
                    neighbor = connection.get_dest(area)
                    if neighbor is None or neighbor.is_blocked:
                        continue
                        
                    cost = connection.cost_to(neighbor)
                    if not self._connection_free(connection, departure, cost):
                        continue
                        
                    n_arrival = departure + cost - 1
                    if not self._area_free(neighbor, n_arrival):
                        continue
                        
                    n_state = (neighbor, n_arrival)
                    if n_state not in best or n_arrival < best[n_state]:
                        best[n_state] = n_arrival
                        previous[n_state] = (state, departure, connection)
                        counter += 1
                        heapq.heappush(queue, (n_arrival, counter, n_state))
                        
        if final_state is None:
            return []
            
        # Reconstruct space-time states backwards from destination
        states = []
        state = final_state
        while state is not None:
            states.append(state)
            record = previous.get(state)
            state = record[0] if record else None
        states.reverse()

        # Build structural physical path and allocate scheduling/reservations
        path = [area for area, _ in states]
        timetable = {}
        for i in range(len(states) - 1):
            area, arrival = states[i]
            _, departure, connection = previous[states[i + 1]]
            cost = connection.cost_to(states[i + 1][0])
            
            timetable[area] = departure
            self._reserve_area(area, arrival, departure)
            self._reserve_connection(connection, departure, cost)
            
        return path, timetable

    def _area_free(self, area, turn) -> bool:
        """
        Checks if a given area has sufficient occupancy capacity at a specific turn.
        Infinite capacity is assumed for structural terminals ('start_hub', 'end_hub').
        """
        if area.is_end or area.role == 'start_hub':
            return True
        return area.reserved.get(turn, 0) < area.max_drones

    def _connection_free(self, connection, departure, cost) -> bool:
        """
        Checks if a connection has available link bandwidth across the entire 
        duration of a prospective crossing.
        """
        for turn in range(departure, departure + cost):
            if connection.reserved.get(turn, 0) >= connection.max_drones:
                return False
        return True

    def _reserve_area(self, area, arrival, departure) -> None:
        """
        Books a drone slot within an area for the duration spanning from 
        its arrival turn up until its departure turn.
        """
        if area.is_end or area.role == 'start_hub':
            return
        for turn in range(arrival, departure):
            area.reserved[turn] = area.reserved.get(turn, 0) + 1

    def _reserve_connection(self, connection, departure, cost) -> None:
        """
        Books a link trajectory slot across a connection for the active time 
        turns required to transit through the link.
        """
        for turn in range(departure, departure + cost):
            connection.reserved[turn] = connection.reserved.get(turn, 0) + 1
