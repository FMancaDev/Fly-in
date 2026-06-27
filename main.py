from src.parser import Parser
from src.pathfinding import Pathfinder


def main() -> None:
    parser = Parser()

    graph, nb_drones = parser.parse(
        "maps/medium/02_circular_loop.txt")

    print("=== GRAPH ===")
    print(f"Drones: {nb_drones}")

    print("\nStart Hub:")
    print(graph.start_hub)

    print("\nEnd HUB:")
    print(graph.end_hub)

    print("\nHub:")
    for hub in graph.hubs.values():
        print(hub)

    print("\nConnections:")
    for connection in graph.connections:
        print(connection)

    Path_finder = Pathfinder()

    path = Path_finder.find_path(
        graph, graph.start_hub, graph.end_hub
    )

    print("\nShortest path:")

    if not path:
        print("No path found")
    else:
        for hub in path:
            print(hub.name)


if __name__ == "__main__":
    main()
