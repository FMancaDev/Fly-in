from typing import List, Tuple, Dict
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
            graph, graph.start_hub, graph.end_hub)

        for i in range(nb_drones):
            self.drones.append(
                Drone(
                    id=i + 1,
                    current_hub=graph.start_hub,
                    target_hub=None,
                    path=list(main_path),
                    path_index=0,
                )
            )

    def simulate_turn(self) -> None:
        self.turn += 1

        for drone in self.drones:
            if drone.delivered:
                continue
            if drone.remaining_turns > 0:
                drone.remaining_turns -= 1
                if drone.remaining_turns == 0 and drone.target_hub is not None:
                    drone.current_hub = drone.target_hub
                    drone.target_hub = None
                    if drone.current_hub in drone.path:
                        drone.path_index = drone.path.index(drone.current_hub)
                    if drone.current_hub == self.graph.end_hub:
                        drone.delivered = True

        hub_occupancy: Dict[str, int] = {}
        for hub_name, hub in self.graph.hubs.items():
            if hub == self.graph.start_hub or hub == self.graph.end_hub:
                continue
            hub_occupancy[hub_name] = sum(
                1 for d in self.drones
                if d.current_hub == hub and d.remaining_turns == 0 and
                not d.delivered and d.target_hub is None
            )

        active_link_usage: Dict[Tuple[str, str], int] = {}
        for other in self.drones:
            if other.target_hub is not None and other.remaining_turns > 0:
                link_key = tuple(
                    sorted((other.current_hub.name, other.target_hub.name)))
                active_link_usage[link_key] = active_link_usage.get(
                    link_key, 0) + 1

        planned_moves: List[Tuple[Drone, Hub, int]] = []
        drones_ready = [
            d for d in self.drones
            if not d.delivered and d.remaining_turns == 0
            and d.current_hub != self.graph.end_hub
        ]

        drones_ready.sort(key=lambda d: (-d.path_index, d.id))

        for drone in drones_ready:
            if drone.path_index + 1 >= len(drone.path):
                continue

            next_hub = drone.path[drone.path_index + 1]

            if (next_hub != self.graph.end_hub and
                    next_hub != self.graph.start_hub):
                if hub_occupancy.get(next_hub.name, 0) >= next_hub.max_drones:
                    continue

            link_key = tuple(sorted((drone.current_hub.name, next_hub.name)))
            connection = next((c for c in self.graph.connections if (
                c.hub1.name, c.hub2.name) == link_key or
                (c.hub2.name, c.hub1.name) == link_key), None)

            if (connection and active_link_usage.get(link_key, 0)
                    >= connection.max_link_capacity):
                continue

            if drone.current_hub != self.graph.start_hub:
                hub_occupancy[drone.current_hub.name] -= 1
            if (next_hub != self.graph.end_hub and
                    next_hub != self.graph.start_hub):
                hub_occupancy[next_hub.name] = hub_occupancy.get(
                    next_hub.name, 0) + 1

            active_link_usage[link_key] = active_link_usage.get(
                link_key, 0) + 1
            travel_time = 2 if next_hub.zone_type == ZoneType.RESTRICTED else 1
            planned_moves.append((drone, next_hub, travel_time))

        for drone, next_hub, travel_time in planned_moves:
            if travel_time == 1:
                drone.current_hub = next_hub
                drone.target_hub = None
                drone.remaining_turns = 0
                drone.path_index += 1

                if drone.current_hub == self.graph.end_hub:
                    drone.delivered = True
            else:
                drone.target_hub = next_hub
                drone.remaining_turns = travel_time

    def all_delivered(self) -> bool:
        return all(drone.delivered for drone in self.drones)

    def run(self) -> None:
        while not self.all_delivered():
            self.simulate_turn()
