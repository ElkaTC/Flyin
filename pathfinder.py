from models import Graph, Area

class Pathfinder:
    def find_path(self,
                  graph: Graph,
                  start: Area,
                  end: Area) -> list[Area]:
        distances = {}
        previous = {}
        for area in graph.areas.values():
            distances[area] = float("inf")
            previous[area] = None
        distances[start] = 0
        unvisited = list(graph.areas.values())
        while unvisited:
            current = min(unvisited, key=lambda area: distances[area])
            unvisited.remove(current)
            if current == end:
                break
            for neighbor in graph.get_neighbors(current):
                if neighbor.is_blocked:
                    continue
                new_distance = distances[current] + neighbor.movement_cost
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    previous[neighbor] = current
        path = []
        current = end
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        return path
                
        
        # for area, distance in distances.items():
        #     print(area.area_id, distance)

        # return []