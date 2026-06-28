from src.graph import Graph, Drone
from src.pathfinding import Pathfinder


class Simulation:
    def __init__(self, graph: Graph, nb_drones: int) -> None:
        self.graph = graph
        self.nb_drones = nb_drones
        self.pathfinder = Pathfinder()
        self.turn = 0
        self.drones: list[Drone] = []

        if self.graph.start_hub is None:
            raise ValueError("Graph has no start_hub")

        if self.graph.end_hub is None:
            raise ValueError("Graph has no end_hub")

        for drone_id in range(1, nb_drones + 1):
            path = self.pathfinder.find_path(
                self.graph,
                self.graph.start_hub,
                self.graph.end_hub
            )

            drone = Drone(
                id=drone_id,
                current_hub=self.graph.start_hub,
                target_hub=None,
                path=path,
                path_index=0
            )
            self.drones.append(drone)

    def run(self) -> None:
        while not self.all_delivered():
            self.simulate_turn()

    def simulate_turn(self) -> None:
        self.turn += 1

        for drone in self.drones:
            if drone.delivered:
                continue

            # drone a espera do outro a frente
            if drone.remaining_turns > 0:
                drone.remaining_turns -= 1

                if drone.remaining_turns == 0:
                    if drone.target_hub is not None:
                        drone.current_hub = drone.target_hub
                        drone.target_hub = None
                        drone.path_index += 1
                continue

            # drone chegou ao destino
            if drone.current_hub == self.graph.end_hub:
                drone.delivered = True
                continue

            # drone pronto para se mover
            if drone.path_index + 1 >= len(drone.path):
                continue

            next_hub = drone.path[drone.path_index + 1]

            # verifica a capacidade do hub destino
            hub_capacity_usage = sum(
                1
                for other in self.drones
                if other.current_hub == next_hub
                and other.remaining_turns == 0
            )

            if hub_capacity_usage >= next_hub.max_drones:
                continue

            # encontrar ligacao correspondente
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

            # verifica a capacidadr da ligacao
            link_usage = sum(
                1
                for other in self.drones
                if other.target_hub == next_hub
                and other.remaining_turns > 0
            )

            if link_usage >= connection.max_link_capacity:
                continue

            # iniciar movimento
            drone.target_hub = next_hub
            if next_hub.zone_type.name == "RESTRICTED":
                drone.remaining_turns = 2
            else:
                drone.remaining_turns = 1

    def all_delivered(self) -> bool:
        return all(drone.delivered for drone in self.drones)
