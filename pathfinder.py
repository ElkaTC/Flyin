import heapq

class Pathfinder:
    def find_path(self, graph, start, end):
        arrival_time = {(start, 0): 0}
        previous = {}
        counter = 0
        queue = [(0, counter, start)]
        visited = set()
        final_time = None
        while queue:
            current_time, _, current_area = heapq.heappop(queue)
            if current_area == end:
                final_time = current_time
                break
            if (current_area, current_time) in visited:
                continue
            visited.add((current_area, current_time))
            for connection in current_area.connections:
                neighbor = connection.get_dest(current_area)
                if neighbor is None or neighbor.is_blocked:
                    continue
                travel = connection.cost_to(neighbor)
                for wait_time in range(100): 
                    departure = current_time + wait_time
                    arrival = departure + travel
                    blocked = False
                    for t in range(departure, arrival):
                        if connection.reserved.get(t, 0) >= connection.max_drones:
                            blocked = True
                            break
                    if not blocked and not neighbor.is_end:
                        if neighbor.reserved.get(arrival, 0) >= neighbor.max_drones:
                            blocked = True
                    if not blocked:
                        neighbor_state = (neighbor, arrival)
                        if neighbor_state not in arrival_time or arrival < arrival_time[neighbor_state]:
                            arrival_time[neighbor_state] = arrival
                            previous[neighbor_state] = (current_area, current_time)
                            counter += 1
                            heapq.heappush(queue, (arrival, counter, neighbor))
                        break
        if final_time is None:
            return []
        path = []
        current_state = (end, final_time)
        while current_state is not None:
            path.append(current_state[0])
            current_state = previous.get(current_state)
        path.reverse()
        time = 0
        timetable = {}
        for i in range(len(path) - 1):
            a = path[i]
            b = path[i + 1]
            connection = graph.get_connection(a, b)
            travel = connection.cost_to(b)
            while True:
                blocked = False
                for t in range(time, time + travel):
                    if connection.reserved.get(t, 0) >= connection.max_drones:
                        blocked = True
                        break
                if not blocked and not b.is_end:
                    if b.reserved.get(time + travel, 0) >= b.max_drones:
                        blocked = True
                if not blocked:
                    break
                time += 1
            timetable[a] = time
            for t in range(time, time + travel):
                connection.reserved[t] = connection.reserved.get(t, 0) + 1
            arrival = time + travel
            if not b.is_end:
                b.reserved[arrival] = b.reserved.get(arrival, 0) + 1
            time = arrival
        print("PATH:", [a.area_id for a in path])
        return path, timetable