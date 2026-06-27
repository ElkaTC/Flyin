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
        for drone in graph.drones:
            path, timetable = pathfinder.find_path(graph, start, end)
            drone.path = path[1:]
            drone.timetable = timetable
        renderer.run()
    except ParseError as e:
        print(e)
        exit(1)