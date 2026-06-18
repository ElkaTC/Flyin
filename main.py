from parsing import MapParser, MapSetting, ParseError
from models import Graph
from visualizer import Renderer
from pathfinder import Pathfinder
        

if __name__ == "__main__":
    try:
        parser = MapParser('test.txt')
        settings = parser.parse()
        graph = Graph.from_settings(settings, parser.nb_drones)
        renderer = Renderer(graph)
        start = graph.get_start_area()
        end = graph.get_end_area()
        pathfinder = Pathfinder()
        path = pathfinder.find_path(graph, start, end)
        print("START:", start.area_id)
        print("END:", end.area_id)
        print("PATH LENGTH:", len(path))
        print("PATH:", [a.area_id for a in path])
        for drone in graph.drones:
            drone.set_path(path)
        renderer.run()
    except ParseError as e:
        print(e)
        exit(1)