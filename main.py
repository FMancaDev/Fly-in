import sys
from src.parser import Parser, ParserError
from src.simulation import Simulation


def print_graph(graph, nb_drones: int) -> None:
    print("=== GRAPH ===")
    print(f"Drones: {nb_drones}")

    print("\nStart Hub:")
    print(graph.start_hub)

    print("\nEnd Hub:")
    print(graph.end_hub)

    print("\nHubs:")
    for hub in graph.hubs.values():
        print(hub)

    print("\nConnections:")
    for connection in graph.connections:
        print(connection)


def print_drones(simulation: Simulation) -> None:
    print("\n=== DRONES ===")

    for drone in simulation.drones:
        path = " -> ".join(
            hub.name for hub in drone.path
        )

        print(
            f"Drone {drone.id}: {path}"
        )


def print_turn(simulation: Simulation) -> None:
    print(f"\nTurn {simulation.turn}")

    for drone in simulation.drones:
        current = (
            drone.current_hub.name
            if drone.current_hub is not None
            else "None"
        )

        target = (
            drone.target_hub.name
            if drone.target_hub is not None
            else "None"
        )

        print(
            f"Drone {drone.id}: "
            f"current={current}, "
            f"target={target}, "
            f"remaining={drone.remaining_turns}, "
            f"delivered={drone.delivered}"
        )


def main() -> None:
    if len(sys.argv) < 2:
        print(
            f"Usage: {sys.argv[0]} <map_file>"
        )
        raise SystemExit(1)

    map_file = sys.argv[1]

    parser = Parser()

    try:
        graph, nb_drones = parser.parse(map_file)
    except FileNotFoundError:
        print(f"Error: file not found: {map_file}")
        raise SystemExit(1)
    except ParserError as error:
        print(f"Parser error: {error}")
        raise SystemExit(1)

    print_graph(graph, nb_drones)

    simulation = Simulation(
        graph,
        nb_drones,
    )

    print_drones(simulation)

    print("\n=== SIMULATION ===")

    while not simulation.all_delivered():
        simulation.simulate_turn()
        print_turn(simulation)

    print(
        f"\nSimulation finished in "
        f"{simulation.turn} turns"
    )


if __name__ == "__main__":
    main()
