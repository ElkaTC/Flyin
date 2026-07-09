import heapq

class Pathfinder:
    HORIZON = 200

    def find_path(self, graph, start, end):
        # Time-expanded Dijkstra in simulation time.
        # A state is (area, arrival) where `arrival` is the simulation turn at
        # which the drone becomes present on `area`. A drone occupies an area
        # from its arrival turn until the turn it departs (exclusive), so the
        # whole stay -- not just the arrival instant -- must fit under the
        # area capacity. Earliest a drone can leave an area is arrival + 1
        # (it cannot depart on the same turn it lands), and crossing an edge of
        # cost c leaving at turn D lands on the neighbor at turn D + c - 1.
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
            for departure in range(arrival + 1, arrival + 1 + self.HORIZON):
                # Staying until `departure` means occupying `area` through turn
                # departure - 1. If that turn is already full the drone cannot
                # remain that long, and neither can it wait any longer.
                if not self._area_free(area, departure - 1):
                    break
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
        states = []
        state = final_state
        while state is not None:
            states.append(state)
            record = previous.get(state)
            state = record[0] if record else None
        states.reverse()

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
        # Start and end hubs are staging/sink areas and are not capacity-limited.
        if area.is_end or area.role == 'start_hub':
            return True
        return area.reserved.get(turn, 0) < area.max_drones

    def _connection_free(self, connection, departure, cost) -> bool:
        for turn in range(departure, departure + cost):
            if connection.reserved.get(turn, 0) >= connection.max_drones:
                return False
        return True

    def _reserve_area(self, area, arrival, departure) -> None:
        if area.is_end or area.role == 'start_hub':
            return
        for turn in range(arrival, departure):
            area.reserved[turn] = area.reserved.get(turn, 0) + 1

    def _reserve_connection(self, connection, departure, cost) -> None:
        for turn in range(departure, departure + cost):
            connection.reserved[turn] = connection.reserved.get(turn, 0) + 1
