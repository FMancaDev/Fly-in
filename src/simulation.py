from src.graph import Graph, Drone, ZoneType
from src.pathfinding import Pathfinder


class Simulation:
    def __init__(self, graph: Graph, nb_drones: int) -> None:
        self.graph = graph
        self.nb_drones = nb_drones
        self.pathfinder = Pathfinder()
        self.turn = 0
        self.drones: list[Drone] = []

        if not graph.start_hub or not graph.end_hub:
            raise ValueError("Graph missing start or end hub")

        main_path = self.pathfinder.find_path(
            graph,
            graph.start_hub,
            graph.end_hub
        )

        alternative_path = []

        if len(main_path) > 2:

            blocked_connections = {
                (main_path[1].name, main_path[2].name),
                (main_path[2].name, main_path[1].name),
            }

            print("blocked_connections:", blocked_connections)

            alternative_path = self.pathfinder.find_path(
                graph,
                graph.start_hub,
                graph.end_hub,
                blocked_connections=blocked_connections
            )

        print("Main path:", [h.name for h in main_path])
        print("Alternative path:", [h.name for h in alternative_path])

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
                    path_index=0
                )
            )

    def simulate_turn(self) -> None:
        self.turn += 1

        for drone in self.drones:
            if drone.delivered:
                continue

            # ainda em movimento
            if drone.remaining_turns > 0:
                drone.remaining_turns -= 1

                if drone.remaining_turns == 0 and drone.target_hub:
                    drone.current_hub = drone.target_hub
                    drone.target_hub = None
                    drone.path_index += 1

                    if drone.current_hub == self.graph.end_hub:
                        drone.delivered = True
                continue

            if drone.current_hub == self.graph.end_hub:
                drone.delivered = True
                continue

            if drone.path_index + 1 >= len(drone.path):
                continue

            next_hub = drone.path[drone.path_index + 1]

            if sum(
                1 for d in self.drones
                if d.current_hub == next_hub and d.remaining_turns == 0
            ) >= next_hub.max_drones:
                continue

            connection = next(
                (
                    c for c in self.graph.connections
                    if (c.hub1 == drone.current_hub and c.hub2 == next_hub)
                    or (c.hub2 == drone.current_hub and c.hub1 == next_hub)
                ),
                None
            )

            if not connection:
                continue

            if sum(
                1 for d in self.drones
                if d.target_hub == next_hub and d.remaining_turns > 0
            ) >= connection.max_link_capacity:
                continue

            drone.target_hub = next_hub
            drone.remaining_turns = 2 if next_hub.zone_type == ZoneType.RESTRICTED else 1

    def all_delivered(self) -> bool:
        return all(d.delivered for d in self.drones)
