from src.parser import Parser
from src.simulation import Simulation


def main() -> None:
    parser = Parser()

    graph, nb_drones = parser.parse(
        "maps/medium/01_dead_end_trap.txt"
    )

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

    simulation = Simulation(graph, nb_drones)

    print("\n=== DRONES ===")
    for drone in simulation.drones:
        print(
            f"Drone {drone.id}: "
            f"{' -> '.join(hub.name for hub in drone.path)}"
        )

    print("\n=== SIMULATION ===")

    while not simulation.all_delivered():
        simulation.simulate_turn()

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

    print(
        f"\nSimulation finished in "
        f"{simulation.turn} turns"
    )


if __name__ == "__main__":
    main()
