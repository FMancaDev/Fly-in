from typing import List, Tuple
from src.graph import Graph, Drone, Hub, ZoneType
from src.pathfinding import Pathfinder


class Simulation:
    def __init__(self, graph: Graph, nb_drones: int) -> None:
        self.graph = graph
        self.nb_drones = nb_drones
        self.pathfinder = Pathfinder()
        self.turn = 0
        self.drones: list[Drone] = []

        if graph.start_hub is None or graph.end_hub is None:
            raise ValueError("Graph missing start or end hub")

        main_path = self.pathfinder.find_path(
            graph,
            graph.start_hub,
            graph.end_hub
        )

        alternative_path: list[Hub] = []

        if len(main_path) > 2:
            blocked_connections = {
                (main_path[1].name, main_path[2].name),
                (main_path[2].name, main_path[1].name),
            }

            alternative_path = self.pathfinder.find_path(
                graph,
                graph.start_hub,
                graph.end_hub,
                blocked_connections=blocked_connections
            )

        for i in range(nb_drones):
            if alternative_path and i % 2 == 1:
                path = alternative_path
            else:
                path = main_path

            self.drones.append(
                Drone(
                    id=i + 1,
                    current_hub=graph.start_hub,
                    target_hub=None,
                    path=path,
                    path_index=0,
                )
            )

    def simulate_turn(self) -> None:
        self.turn += 1

        planned_moves: List[Tuple[Drone, Hub, int]] = []

        for drone in self.drones:
            if drone.delivered:
                continue

            if drone.remaining_turns > 0:
                drone.remaining_turns -= 1

                if drone.remaining_turns == 0 and drone.target_hub is not None:
                    drone.current_hub = drone.target_hub
                    drone.target_hub = None
                    drone.path_index += 1

                    if drone.current_hub == self.graph.end_hub:
                        drone.delivered = True

        for drone in self.drones:
            if drone.delivered:
                continue

            if drone.remaining_turns > 0:
                continue

            if drone.current_hub == self.graph.end_hub:
                drone.delivered = True
                continue

            if drone.path_index + 1 >= len(drone.path):
                continue

            next_hub = drone.path[drone.path_index + 1]

            hub_usage = sum(
                1
                for other in self.drones
                if (
                    other.current_hub == next_hub
                    and other.remaining_turns == 0
                    and not other.delivered
                    and other.target_hub is None
                )
            )

            incoming = sum(
                1
                for _, planned_hub, _ in planned_moves
                if planned_hub == next_hub
            )

            if hub_usage + incoming >= next_hub.max_drones:
                continue

            connection = next(
                (
                    conn
                    for conn in self.graph.connections
                    if (
                        conn.hub1 == drone.current_hub
                        and conn.hub2 == next_hub
                    )
                    or (
                        conn.hub2 == drone.current_hub
                        and conn.hub1 == next_hub
                    )
                ),
                None,
            )

            if connection is None:
                continue

            link_usage = sum(
                1
                for other in self.drones
                if (
                    other.target_hub == next_hub
                    and other.remaining_turns > 0
                )
            )

            if link_usage >= connection.max_link_capacity:
                continue

            travel_time = (
                2
                if next_hub.zone_type == ZoneType.RESTRICTED
                else 1
            )

            planned_moves.append(
                (
                    drone,
                    next_hub,
                    travel_time,
                )
            )

        for drone, next_hub, travel_time in planned_moves:
            drone.target_hub = next_hub
            drone.remaining_turns = travel_time

    def all_delivered(self) -> bool:
        return all(drone.delivered for drone in self.drones)

    def run(self) -> None:
        while not self.all_delivered():
            self.simulate_turn()
