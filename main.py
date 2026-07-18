import argparse

from src.parser import Parser, ParserError
from src.renderer import Renderer
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

    return parser.parse_args()


def run_terminal(simulation: Simulation) -> None:
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


def main() -> None:
    args = parse_arguments()

    parser = Parser()

    try:
        graph, nb_drones = parser.parse(args.map_file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.map_file}")
        raise SystemExit(1)
    except ParserError as error:
        print(f"Parser error: {error}")
        raise SystemExit(1)

    simulation = Simulation(graph, nb_drones)

    if args.graphics:
        renderer = Renderer(graph, simulation)
        renderer.run()
    else:
        run_terminal(simulation)


if __name__ == "__main__":
    main()
