class Pathfinder:
    def find_path(self, graph, start, end):

        arrival_time = {}
        previous = {}
        departure_time = {}
        for area in graph.areas.values():
            arrival_time[area] = float("inf")
            previous[area] = None
            departure_time[area] = 0
        arrival_time[start] = 0
        departure_time[start] = 0
        unvisited = list(graph.areas.values())
        while unvisited:
            current = min(unvisited, key=lambda a: arrival_time[a])
            unvisited.remove(current)
            if arrival_time[current] == float("inf"):
                break
            for connection in current.connections:
                neighbor = connection.get_dest(current)
                if neighbor is None or neighbor.is_blocked:
                    continue
                travel = connection.cost_to(neighbor)
                departure = arrival_time[current]
                while True:
                    arrival = departure + travel
                    blocked = False
                    for t in range(departure, arrival):
                        if connection.reserved.get(t, 0) >= connection.max_drones:
                            blocked = True
                            break
                    if not neighbor.is_end and neighbor.reserved.get(arrival, 0) >= neighbor.max_drones:
                        blocked = True
                    if not blocked:
                        break
                    departure += 1
                if arrival < arrival_time[neighbor]:
                    arrival_time[neighbor] = arrival
                    departure_time[neighbor] = departure
                    previous[neighbor] = current
        if arrival_time[end] == float("inf"):
            return []
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous[current]

        path.reverse()
        time = departure_time[path[0]]
        for i in range(len(path) - 1):
            a = path[i]
            b = path[i + 1]
            connection = graph.get_connection(a, b)
            travel = connection.cost_to(b)
            for t in range(time, time + travel):
                connection.reserved[t] = connection.reserved.get(t, 0) + 1
            arrival = time + travel
            if not b.is_end:
                b.reserved[arrival] = b.reserved.get(arrival, 0) + 1
            time = arrival
        print("PATH:", [a.area_id for a in path])
        return path