from typing import List, Tuple, Set, Dict
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
            path = alternative_path if (
                alternative_path and i % 2 == 1) else main_path
            self.drones.append(
                Drone(
                    id=i + 1,
                    current_hub=graph.start_hub,
                    target_hub=None,
                    path=list(path),
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
                    else:
                        drone.path_index = 0

                    if drone.current_hub == self.graph.end_hub:
                        drone.delivered = True

        current_hub_occupancy: Dict[str, int] = {}
        for hub_name, hub in self.graph.hubs.items():
            if hub == self.graph.start_hub or hub == self.graph.end_hub:
                continue
            count = sum(
                1 for d in self.drones
                if d.current_hub == hub and d.remaining_turns == 0 and not d.delivered and d.target_hub is None
            )
            current_hub_occupancy[hub_name] = count

        future_hub_incoming: Dict[str, int] = {}
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
            if not d.delivered and d.remaining_turns == 0 and d.current_hub != self.graph.end_hub
        ]

        def get_distance_priority(d: Drone) -> Tuple[int, int, int]:
            is_at_start = 1 if d.current_hub == self.graph.start_hub else 0
            p = self.pathfinder.find_path(
                self.graph, d.current_hub, self.graph.end_hub)
            dist = len(p) if p else 999
            return (is_at_start, dist, -d.id)

        drones_ready.sort(key=get_distance_priority)

        while True:
            moved_any = False
            for drone in drones_ready:
                if drone in [move[0] for move in planned_moves]:
                    continue

                next_hub = None
                if drone.path:
                    try:
                        idx = drone.path.index(drone.current_hub)
                        if idx + 1 < len(drone.path):
                            next_hub = drone.path[idx + 1]
                    except ValueError:
                        pass

                if next_hub is None:
                    new_path = self.pathfinder.find_path(
                        self.graph, drone.current_hub, self.graph.end_hub)
                    if new_path and len(new_path) >= 2:
                        drone.path = list(new_path)
                        next_hub = drone.path[1]
                    else:
                        continue

                if next_hub != self.graph.end_hub and next_hub != self.graph.start_hub:
                    dest_occupancy = current_hub_occupancy.get(
                        next_hub.name, 0) + future_hub_incoming.get(next_hub.name, 0)

                    if dest_occupancy >= next_hub.max_drones:
                        blocked_hubs = {next_hub.name}
                        alt_path = self.pathfinder.find_path(
                            self.graph, drone.current_hub, self.graph.end_hub, blocked_hubs=blocked_hubs)

                        if alt_path and len(alt_path) >= 2:
                            drone.path = list(alt_path)
                            next_hub = alt_path[1]
                        else:
                            if current_hub_occupancy.get(next_hub.name, 0) + future_hub_incoming.get(next_hub.name, 0) >= next_hub.max_drones:
                                continue

                connection = next(
                    (conn for conn in self.graph.connections
                     if (conn.hub1 == drone.current_hub and conn.hub2 == next_hub) or
                        (conn.hub2 == drone.current_hub and conn.hub1 == next_hub)),
                    None
                )
                if connection is None:
                    continue

                link_key = tuple(
                    sorted((drone.current_hub.name, next_hub.name)))
                if active_link_usage.get(link_key, 0) >= connection.max_link_capacity:
                    continue

                if drone.current_hub != self.graph.start_hub:
                    if drone.current_hub.name in current_hub_occupancy:
                        current_hub_occupancy[drone.current_hub.name] = max(
                            0, current_hub_occupancy[drone.current_hub.name] - 1)

                if next_hub != self.graph.end_hub and next_hub != self.graph.start_hub:
                    future_hub_incoming[next_hub.name] = future_hub_incoming.get(
                        next_hub.name, 0) + 1
                active_link_usage[link_key] = active_link_usage.get(
                    link_key, 0) + 1

                travel_time = 2 if next_hub.zone_type == ZoneType.RESTRICTED else 1
                planned_moves.append((drone, next_hub, travel_time))
                moved_any = True

            if not moved_any:
                break

        for drone, next_hub, travel_time in planned_moves:
            drone.target_hub = next_hub
            drone.remaining_turns = travel_time

    def all_delivered(self) -> bool:
        return all(drone.delivered for drone in self.drones)

    def run(self) -> None:
        while not self.all_delivered():
            self.simulate_turn()
