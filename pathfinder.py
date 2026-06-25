from models import Area

class Pathfinder:
    def find_path(self,
                  graph,
                  start: Area,
                  end: Area) -> list[Area]:
        arrival_time = {}
        previous = {}
        for area in graph.areas.values():
            arrival_time[area] = float("inf")
            previous[area] = None
        arrival_time[start] = 0
        unvisited = list(graph.areas.values())
        while unvisited:
            current = min(
                unvisited,
                key=lambda area: arrival_time[area]
            )
            unvisited.remove(current)
            if current == end:
                break
            if arrival_time[current] == float("inf"):
                break
            for connection in current.connections:
                neighbor = connection.get_dest(current)
                if neighbor is None:
                    continue
                if neighbor.is_blocked:
                    continue
                travel_time = connection.cost_to(neighbor)
                new_arrival =  arrival_time[current] + travel_time
                if (not neighbor.is_end
                    and neighbor.reservations.get(new_arrival, 0)
                    >= neighbor.max_drones):
                    continue
                if new_arrival < arrival_time[neighbor]:
                    arrival_time[neighbor] = new_arrival
                    previous[neighbor] = current
        if arrival_time[end] == float("inf"):
            return[]
        current = end
        path = []
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        print("PATH:", [area.area_id for area in path])
        return path