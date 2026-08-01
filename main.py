import argparse

from src.graph import Connection, Graph, Hub
from src.parser import Parser, ParserError
from src.simulation import Simulation


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fly-in drone simulation"
    )

    parser.add_argument(
        "map_file",
        help="Path to the map file",
    )

    parser.add_argument(
        "--graphics",
        action="store_true",
        help="Open the Pygame visualizer",
    )

    parser.add_argument(
        "--capacity-info",
        action="store_true",
        help="Display hub and connection capacity usage",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the map without running the simulation",
    )

    return parser.parse_args()


def hub_usage(
    graph: Graph,
    simulation: Simulation,
    hub: Hub,
) -> int:
    if hub == graph.end_hub:
        return sum(
            1
            for drone in simulation.drones
            if drone.delivered
        )

    return sum(
        1
        for drone in simulation.drones
        if (
            not drone.delivered
            and drone.current_hub == hub
            and drone.target_hub is None
        )
    )


def connection_usage(
    simulation: Simulation,
    connection: Connection,
) -> int:
    connection_hubs = {
        connection.hub1.name,
        connection.hub2.name,
    }

    usage = 0

    for drone in simulation.drones:
        if drone.delivered:
            continue

        if drone.current_hub is None:
            continue

        if drone.target_hub is None:
            continue

        drone_hubs = {
            drone.current_hub.name,
            drone.target_hub.name,
        }

        if drone_hubs == connection_hubs:
            usage += 1

    return usage


def print_capacity_info(
    graph: Graph,
    simulation: Simulation,
) -> None:
    print("\nCapacity information:")

    print("  Hubs:")

    for hub in graph.hubs.values():
        usage = hub_usage(
            graph,
            simulation,
            hub,
        )

        print(
            f"    {hub.name}: "
            f"{usage}/{hub.max_drones} drones"
        )

    print("  Connections:")

    for connection in graph.connections:
        usage = connection_usage(
            simulation,
            connection,
        )

        print(
            f"    {connection.hub1.name}"
            f"-{connection.hub2.name}: "
            f"{usage}/"
            f"{connection.max_link_capacity} capacity used"
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


def run_terminal(
    graph: Graph,
    simulation: Simulation,
    capacity_info: bool,
) -> None:
    while not simulation.all_delivered():
        simulation.simulate_turn()

        print_turn(simulation)

        if capacity_info:
            print_capacity_info(
                graph,
                simulation,
            )

    print(
        f"\nSimulation finished in "
        f"{simulation.turn} turns"
    )


def run_dry_run(
    graph: Graph,
    nb_drones: int,
) -> None:
    print("Map parsed successfully.")
    print(f"Drones: {nb_drones}")
    print(f"Hubs: {len(graph.hubs)}")
    print(f"Connections: {len(graph.connections)}")

    if graph.start_hub is not None:
        print(f"Start hub: {graph.start_hub.name}")

    if graph.end_hub is not None:
        print(f"End hub: {graph.end_hub.name}")


def run_graphics(
    graph: Graph,
    simulation: Simulation,
) -> None:
    from src.renderer import Renderer

    renderer = Renderer(
        graph,
        simulation,
    )
    renderer.run()


def main() -> None:
    args = parse_arguments()

    parser = Parser()

    try:
        graph, nb_drones = parser.parse(
            args.map_file
        )
    except FileNotFoundError:
        print(
            f"Error: file not found: "
            f"{args.map_file}"
        )
        raise SystemExit(1)
    except ParserError as error:
        print(f"Parser error: {error}")
        raise SystemExit(1)

    if args.dry_run:
        run_dry_run(
            graph,
            nb_drones,
        )
        return

    simulation = Simulation(
        graph,
        nb_drones,
    )

    if args.graphics:
        run_graphics(
            graph,
            simulation,
        )
    else:
        run_terminal(
            graph,
            simulation,
            args.capacity_info,
        )


if __name__ == "__main__":
    main()
