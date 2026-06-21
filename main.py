from src.parser import Parser


def main() -> None:
    parser = Parser()

    graph, nb_drones = parser.parse("maps/test.map")

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


if __name__ == "__main__":
    main()
